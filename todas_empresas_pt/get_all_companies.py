"""
Base de Dados Incremental de Empresas Portuguesas — com backfill histórico
============================================================================

O QUE ISTO FAZ:

- Mantém um ponteiro de progresso (todas_empresas_pt/progress.json) começando em
  Janeiro de 2020. Em cada execução diária, processa UM mês e avança o ponteiro.
- Para meses passados: usa o Arquivo.pt (arquivo.pt), o arquivo público da web
  portuguesa, para obter cópias históricas da página de "novas empresas" da
  eInforma tal como existiam nessa altura, e extrai as empresas listadas nelas.
- Quando o ponteiro alcança o mês atual: passa a usar o modo "ao vivo" (scraping
  direto da eInforma, como antes), porque não há arquivo do mês corrente.
- Tudo o que é novo (por NIF) é acrescentado a empresas_db.csv. Nada é reescrito
  nem apagado.

LIMITAÇÃO HONESTA (importante):
A página da eInforma só mostra uma janela rolante dos últimos ~7 dias. Uma cópia
arquivada de um mês só captura essa janela de 7 dias no momento exato em que o
Arquivo.pt visitou a página — não o mês inteiro. Se o Arquivo.pt só visitou essa
página 2 ou 3 vezes nesse mês, só teremos empresas dessas datas específicas, não
de todo o mês. O script reporta sempre, nos logs, quantas cópias (snapshots)
encontrou e quantas empresas extraiu, para nunca esconder um resultado fraco ou
vazio atrás de um "sucesso" do workflow.
"""

import asyncio
import csv
import json
import os
import re
from datetime import datetime, timedelta
from pathlib import Path

import pytz
import requests
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

BASE_DIR = Path(__file__).parent
DB_PATH = BASE_DIR / "empresas_db.csv"
PROGRESS_PATH = BASE_DIR / "progress.json"
FIELDNAMES = ["nif", "name", "location", "activity", "first_seen", "source", "justica_link"]

LISBON_TZ = pytz.timezone("Europe/Lisbon")
EINFORMA_TARGET = "www.einforma.pt/novas-empresas-portuguesas"
CDX_URL = "https://arquivo.pt/wayback/cdx"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"

DATE_NAME_RE = re.compile(r"(\d{2}-\d{2}-\d{4})\s*-\s*(.+)")


# ---------------------------------------------------------------------------
# Progresso (que mês estamos a processar)
# ---------------------------------------------------------------------------

def load_progress():
    if not PROGRESS_PATH.exists():
        return {"year": 2020, "month": 1}
    with open(PROGRESS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_progress(year, month):
    with open(PROGRESS_PATH, "w", encoding="utf-8") as f:
        json.dump({"year": year, "month": month}, f)


def next_month(year, month):
    if month == 12:
        return year + 1, 1
    return year, month + 1


def is_current_or_future_month(year, month):
    now = datetime.now(LISBON_TZ)
    return (year, month) >= (now.year, now.month)


# ---------------------------------------------------------------------------
# Modo histórico: Arquivo.pt
# ---------------------------------------------------------------------------

def get_snapshots_for_month(year, month):
    """Queries Arquivo.pt's CDX API for archived captures of the einforma page in a given month."""
    from_ts = f"{year}{month:02d}01"
    y2, m2 = next_month(year, month)
    to_ts = f"{y2}{m2:02d}01"

    params = {
        "url": EINFORMA_TARGET,
        "from": from_ts,
        "to": to_ts,
        "output": "json",
    }
    try:
        resp = requests.get(CDX_URL, params=params, timeout=30, headers={"User-Agent": UA})
        resp.raise_for_status()
        rows = resp.json()
    except Exception as e:
        print(f"Erro a consultar o Arquivo.pt CDX para {year}-{month:02d}: {e}")
        return []

    if not rows or len(rows) < 2:
        return []

    header = rows[0]
    try:
        ts_idx = header.index("timestamp")
        orig_idx = header.index("original")
    except ValueError:
        print(f"Formato de resposta CDX inesperado: {header}")
        return []

    return [(r[ts_idx], r[orig_idx]) for r in rows[1:]]


def fetch_archived_html(timestamp, original_url):
    replay_url = f"https://arquivo.pt/wayback/{timestamp}/{original_url}"
    resp = requests.get(replay_url, timeout=30, headers={"User-Agent": UA})
    resp.raise_for_status()
    return resp.text


def parse_companies_from_html(html):
    soup = BeautifulSoup(html, "html.parser")
    companies = []
    for a in soup.select("a[href*='ETIQUETA_EMPRESA']"):
        text = a.get_text(strip=True)
        href = a.get("href", "")
        match = DATE_NAME_RE.match(text)
        if not match:
            continue
        date_str, name = match.groups()
        nif = href.rstrip("/").split("/")[-1]
        if not nif.isdigit():
            continue
        companies.append({"nif": nif, "name": name, "date": date_str, "href": href, "location": "N/A", "activity": "N/A"})
    return companies


def get_companies_from_archive(year, month):
    snapshots = get_snapshots_for_month(year, month)
    print(f"Arquivo.pt: {len(snapshots)} cópias encontradas para {year}-{month:02d}.")

    all_companies = {}
    for timestamp, original_url in snapshots:
        try:
            html = fetch_archived_html(timestamp, original_url)
        except Exception as e:
            print(f"  Falha ao obter cópia de {timestamp}: {e}")
            continue
        found = parse_companies_from_html(html)
        print(f"  Cópia {timestamp}: {len(found)} empresas listadas.")
        for c in found:
            all_companies[c["nif"]] = c

    result = list(all_companies.values())
    print(f"Arquivo.pt total único para {year}-{month:02d}: {len(result)} empresas.")
    return result


# ---------------------------------------------------------------------------
# Modo ao vivo (mês atual): mesma lógica já usada e testada em produção
# ---------------------------------------------------------------------------

async def get_companies_live():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
            )
        )
        page = await context.new_page()

        print("Acesso ao vivo à eInforma (novas empresas)...")
        await page.goto("https://www.einforma.pt/novas-empresas-portuguesas")
        await page.wait_for_selector("ul li a[href*='ETIQUETA_EMPRESA']")

        links = await page.query_selector_all("ul li a[href*='ETIQUETA_EMPRESA']")

        candidate_dates = [
            (datetime.now(LISBON_TZ) - timedelta(days=d)).strftime("%d-%m-%Y") for d in range(7)
        ]
        print(f"Janela de datas: {candidate_dates[0]} .. {candidate_dates[-1]}")

        companies = []
        for link in links:
            text = await link.inner_text()
            if any(d in text for d in candidate_dates):
                href = await link.get_attribute("href")
                nif = href.split("/")[-1] if "/" in href else ""
                name = text.split(" - ", 1)[-1] if " - " in text else text
                companies.append({"name": name, "nif": nif, "url": f"https://www.einforma.pt{href}"})

        print(f"Ao vivo: {len(companies)} empresas na janela de 7 dias.")

        final_list = []
        for comp in companies:
            try:
                await page.goto(comp["url"], timeout=10000)
                loc_elem = await page.query_selector("text='Morada:' >> xpath=..")
                comp["location"] = (
                    (await loc_elem.inner_text()).replace("Morada:", "").strip() if loc_elem else "N/A"
                )
                act_elem = await page.query_selector("text='Atividade (CAE):' >> xpath=..")
                comp["activity"] = (
                    (await act_elem.inner_text()).replace("Atividade (CAE):", "").strip() if act_elem else "N/A"
                )
                final_list.append(comp)
            except Exception as e:
                print(f"  Erro a obter detalhes de {comp['name']}: {e}")

        await browser.close()
        return final_list


# ---------------------------------------------------------------------------
# Base de dados persistente
# ---------------------------------------------------------------------------

def load_existing_nifs():
    if not DB_PATH.exists():
        with open(DB_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        return set()
    with open(DB_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["nif"] for row in reader if row.get("nif")}


def append_new_companies(companies, source_label):
    existing_nifs = load_existing_nifs()
    today_str = datetime.now(LISBON_TZ).strftime("%Y-%m-%d")

    new_rows = []
    for c in companies:
        nif = c.get("nif", "")
        if not nif or nif in existing_nifs:
            continue
        new_rows.append(
            {
                "nif": nif,
                "name": c.get("name", ""),
                "location": c.get("location", "N/A"),
                "activity": c.get("activity", "N/A"),
                "first_seen": today_str,
                "source": source_label,
                "justica_link": f"https://publicacoes.mj.pt/Pesquisa.aspx?nif={nif}",
            }
        )
        existing_nifs.add(nif)

    if new_rows:
        with open(DB_PATH, "a", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writerows(new_rows)

    return new_rows


def count_total_companies():
    if not DB_PATH.exists():
        return 0
    with open(DB_PATH, "r", newline="", encoding="utf-8") as f:
        return sum(1 for _ in csv.DictReader(f))


# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------

def send_email(new_rows, total_count, period_label):
    account_email = "hugo.galaz.ferreira@gmail.com"
    receiver_emails = ["geral@hugogalaz.pt", "davidafpinto@me.com"]
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not password:
        print("GMAIL_APP_PASSWORD não definida. Email não enviado.")
        return

    msg = MIMEMultipart()
    msg["From"] = account_email
    msg["To"] = ", ".join(receiver_emails)
    msg["Subject"] = (
        f"Base de Empresas PT [{period_label}] — {len(new_rows)} novas, {total_count} no total "
        f"— {datetime.now(LISBON_TZ).strftime('%d/%m/%Y')}"
    )

    html = f"""
    <html><head><style>
        table {{ border-collapse: collapse; width: 100%; font-family: 'Segoe UI', Arial, sans-serif; }}
        th {{ background-color: #004a99; color: white; padding: 12px; text-align: left; font-size: 14px; }}
        td {{ border: 1px solid #dddddd; padding: 10px; font-size: 13px; color: #333; }}
        tr:nth-child(even) {{ background-color: #f9f9f9; }}
        h2 {{ color: #004a99; border-bottom: 2px solid #004a99; padding-bottom: 10px; }}
        .stat {{ font-size: 15px; color: #004a99; font-weight: bold; }}
        .nif {{ color: #666; font-size: 11px; }}
    </style></head><body>
        <h2>Base de Dados de Empresas Portuguesas</h2>
        <p class="stat">Período processado hoje: {period_label}</p>
        <p class="stat">Total acumulado na base: {total_count} empresas</p>
        <p>Novas empresas adicionadas hoje: {len(new_rows)}</p>
        <table><tr><th>Nome</th><th>Localidade</th><th>Atividade</th></tr>
    """
    if not new_rows:
        html += "<tr><td colspan='3' style='text-align:center;'>Nenhuma empresa nova encontrada neste período.</td></tr>"
    else:
        for c in new_rows:
            html += f"""<tr><td><b>{c['name']}</b><br><span class="nif">NIF: {c['nif']}</span></td>
                <td>{c['location']}</td><td>{c['activity']}</td></tr>"""
    html += "</table></body></html>"

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(account_email, password)
            server.send_message(msg)
        print("Email enviado com sucesso!")
    except Exception as e:
        print(f"Erro ao enviar email: {e}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    print(f"Início: {datetime.now(LISBON_TZ)}")
    progress = load_progress()
    year, month = progress["year"], progress["month"]

    try:
        if is_current_or_future_month(year, month):
            period_label = f"ao vivo ({datetime.now(LISBON_TZ).strftime('%Y-%m')})"
            print(f"Ponteiro alcançou o mês atual — a usar modo ao vivo.")
            companies = await get_companies_live()
            new_rows = append_new_companies(companies, source_label="live")
            # não avança o progresso: fica em modo ao vivo todos os dias seguintes
        else:
            period_label = f"arquivo histórico {year}-{month:02d}"
            print(f"A processar mês histórico: {year}-{month:02d}")
            companies = get_companies_from_archive(year, month)
            new_rows = append_new_companies(companies, source_label=f"arquivo.pt {year}-{month:02d}")
            save_progress(*next_month(year, month))
            print(f"Progresso avançado para: {next_month(year, month)}")

        total = count_total_companies()
        print(f"Novas empresas adicionadas: {len(new_rows)}. Total na base: {total}")
        send_email(new_rows, total, period_label)

    except Exception as e:
        print(f"Erro fatal na execução: {e}")


if __name__ == "__main__":
    asyncio.run(main())
