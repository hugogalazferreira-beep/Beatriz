"""
Base de Dados Incremental de Empresas Portuguesas
==================================================

O QUE ISTO FAZ (e o que NÃO faz):

- Usa a MESMA página pública que já usas em main.py (einforma.pt/novas-empresas-portuguesas),
  que lista empresas recém-criadas nas últimas ~48h. Não faz scraping em massa, não itera por
  CAE nem distrito, não tenta contornar bloqueios anti-bot de nenhum site.
- Cada vez que corre, adiciona ao ficheiro empresas_db.csv apenas as empresas que ainda não
  lá estavam (deduplicação por NIF). Isto significa que a base de dados CRESCE com o tempo,
  a partir de hoje. NÃO contém as ~500 mil empresas já existentes em Portugal — isso não é
  possível obter de forma gratuita e sem violar termos de serviço de terceiros (ver conversa).
- Envia um email diário com: as empresas novas de hoje + o total acumulado na base.

Este ficheiro é completamente independente do main.py (projeto "novas empresas"), que
permanece intocado.
"""

import asyncio
import csv
import os
from datetime import datetime, timedelta
from pathlib import Path

import pytz
from playwright.async_api import async_playwright
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

DB_PATH = Path(__file__).parent / "empresas_db.csv"
FIELDNAMES = ["nif", "name", "location", "activity", "first_seen", "justica_link"]

LISBON_TZ = pytz.timezone("Europe/Lisbon")


async def get_companies_from_einforma():
    """
    Scrapes the list of newly registered companies from einforma.pt.
    Same proven source/selectors as main.py's get_companies_from_einforma().
    Only covers the last ~48h feed the site publicly exposes — this is a
    'new companies' feed, not a full directory.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) "
                "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1"
            )
        )
        page = await context.new_page()

        print("Accessing einforma for new companies...")
        await page.goto("https://www.einforma.pt/novas-empresas-portuguesas")
        await page.wait_for_selector("ul li a[href*='ETIQUETA_EMPRESA']")

        links = await page.query_selector_all("ul li a[href*='ETIQUETA_EMPRESA']")

        today_str = datetime.now(LISBON_TZ).strftime("%d-%m-%Y")
        yesterday_str = (datetime.now(LISBON_TZ) - timedelta(days=1)).strftime("%d-%m-%Y")

        print(f"Filtering for dates: {today_str} or {yesterday_str}")

        companies = []
        for link in links:
            text = await link.inner_text()
            if today_str in text or yesterday_str in text:
                href = await link.get_attribute("href")
                nif = href.split("/")[-1] if "/" in href else ""
                name = text.split(" - ", 1)[-1] if " - " in text else text
                companies.append({"name": name, "nif": nif, "url": f"https://www.einforma.pt{href}"})

        final_list = []
        print(f"Enriching {len(companies)} companies...")
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
                print(f"Error fetching details for {comp['name']}: {e}")

        await browser.close()
        return final_list


def load_existing_nifs():
    """Returns the set of NIFs already stored, and creates the CSV with headers if missing."""
    if not DB_PATH.exists():
        with open(DB_PATH, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
            writer.writeheader()
        return set()

    with open(DB_PATH, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        return {row["nif"] for row in reader if row.get("nif")}


def append_new_companies(companies):
    """
    Appends only companies whose NIF is not already in the database.
    Returns the list of companies actually added.
    """
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


def send_email(new_rows, total_count):
    sender_email = "hugo.galaz.ferreira@gmail.com"  # actual Gmail account tied to the app password
    from_display = "beatriz@gfconsulting.pt"  # must be a verified "Send As" alias in Gmail settings
    receiver_emails = ["geral@hugogalaz.pt", "davidafpinto@me.com"]
    password = os.environ.get("GMAIL_APP_PASSWORD")

    if not password:
        print("GMAIL_APP_PASSWORD not set. Skipping email.")
        return

    msg = MIMEMultipart()
    msg["From"] = f"Base de Empresas PT <{from_display}>"
    msg["To"] = ", ".join(receiver_emails)
    msg["Subject"] = (
        f"Base de Empresas PT — {len(new_rows)} novas hoje, {total_count} no total "
        f"— {datetime.now(LISBON_TZ).strftime('%d/%m/%Y')}"
    )

    html = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Segoe UI', Arial, sans-serif; }}
            th {{ background-color: #004a99; color: white; padding: 12px; text-align: left; font-size: 14px; }}
            td {{ border: 1px solid #dddddd; padding: 10px; font-size: 13px; color: #333; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            h2 {{ color: #004a99; border-bottom: 2px solid #004a99; padding-bottom: 10px; }}
            .stat {{ font-size: 15px; color: #004a99; font-weight: bold; }}
            .nif {{ color: #666; font-size: 11px; }}
        </style>
    </head>
    <body>
        <h2>Base de Dados de Empresas Portuguesas</h2>
        <p class="stat">Total acumulado na base: {total_count} empresas</p>
        <p>Novas empresas adicionadas hoje: {len(new_rows)}</p>
        <table>
            <tr>
                <th>Nome da empresa</th>
                <th>Localidade</th>
                <th>Área de atividade</th>
            </tr>
    """

    if not new_rows:
        html += "<tr><td colspan='3' style='text-align: center;'>Nenhuma empresa nova detetada hoje.</td></tr>"
    else:
        for c in new_rows:
            html += f"""
                <tr>
                    <td><b>{c['name']}</b><br><span class="nif">NIF: {c['nif']}</span></td>
                    <td>{c['location']}</td>
                    <td>{c['activity']}</td>
                </tr>
            """

    html += """
        </table>
        <br>
        <p><i>Base construída incrementalmente a partir de empresas registadas publicamente.
        Não inclui empresas anteriores ao início desta recolha.</i></p>
    </body>
    </html>
    """

    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")


async def main():
    print(f"Agent started at {datetime.now(LISBON_TZ)}")
    try:
        companies = await get_companies_from_einforma()
        print(f"Total companies scraped from feed: {len(companies)}")
        new_rows = append_new_companies(companies)
        total = count_total_companies()
        print(f"New companies added to DB: {len(new_rows)}. Total in DB: {total}")
        send_email(new_rows, total)
    except Exception as e:
        print(f"Fatal error in agent execution: {e}")


if __name__ == "__main__":
    asyncio.run(main())
