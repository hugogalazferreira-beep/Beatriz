import asyncio
from playwright.async_api import async_playwright
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import os
from datetime import datetime, timedelta
import pytz

async def get_companies_from_einforma():
    """
    Scrapes the list of new companies from einforma.pt.
    This is a reliable way to get the names and NIFs of companies created in the last 24h.
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        # Using a mobile user agent can sometimes bypass desktop-specific protections
        context = await browser.new_context(user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.4 Mobile/15E148 Safari/604.1")
        page = await context.new_page()
        
        print("Accessing einforma for new companies...")
        await page.goto("https://www.einforma.pt/novas-empresas-portuguesas")
        await page.wait_for_selector("ul li a[href*='ETIQUETA_EMPRESA']")
        
        links = await page.query_selector_all("ul li a[href*='ETIQUETA_EMPRESA']")
        
        # We check both today and yesterday dates to cover the full 24h
        today_str = datetime.now(pytz.timezone('Europe/Lisbon')).strftime("%d-%m-%Y")
        yesterday_str = (datetime.now(pytz.timezone('Europe/Lisbon')) - timedelta(days=1)).strftime("%d-%m-%Y")
        
        print(f"Filtering for dates: {today_str} or {yesterday_str}")
        
        companies = []
        for link in links:
            text = await link.inner_text()
            if today_str in text or yesterday_str in text:
                href = await link.get_attribute("href")
                # href structure: /servlet/app/portal/ENTP/prod/ETIQUETA_EMPRESA/nif/519297288
                nif = href.split("/")[-1] if "/" in href else ""
                name = text.split(" - ", 1)[-1] if " - " in text else text
                companies.append({"name": name, "nif": nif, "url": f"https://www.einforma.pt{href}"})
        
        final_list = []
        print(f"Enriching {len(companies)} companies...")
        for comp in companies:
            try:
                await page.goto(comp['url'], timeout=10000)
                
                # Extract basic info
                loc_elem = await page.query_selector("text='Morada:' >> xpath=..")
                comp['location'] = (await loc_elem.inner_text()).replace("Morada:", "").strip() if loc_elem else "N/A"
                
                act_elem = await page.query_selector("text='Atividade (CAE):' >> xpath=..")
                comp['activity'] = (await act_elem.inner_text()).replace("Atividade (CAE):", "").strip() if act_elem else "N/A"
                
                # Placeholder for data that is generally not public without registered account/payment
                comp['responsible'] = "Desconhecido"
                comp['contacts'] = "N/A"
                
                final_list.append(comp)
            except Exception as e:
                print(f"Error fetching details for {comp['name']}: {e}")
                
        await browser.close()
        return final_list

def send_email(companies):
    sender_email = "hugo.galaz.ferreira@gmail.com"
    receiver_email = "geral@hugogalaz.pt"
    password = os.environ.get("GMAIL_APP_PASSWORD")
    
    if not password:
        print("GMAIL_APP_PASSWORD not set. Skipping email.")
        return

    msg = MIMEMultipart()
    msg['From'] = f"Agente Portugal Empresas <{sender_email}>"
    msg['To'] = receiver_email
    msg['Subject'] = f"🚀 Lista de Novas Empresas em Portugal - {datetime.now(pytz.timezone('Europe/Lisbon')).strftime('%d/%m/%Y')}"
    
    html = f"""
    <html>
    <head>
        <style>
            table {{ border-collapse: collapse; width: 100%; font-family: 'Segoe UI', Arial, sans-serif; }}
            th {{ background-color: #004a99; color: white; padding: 12px; text-align: left; font-size: 14px; }}
            td {{ border: 1px solid #dddddd; padding: 10px; font-size: 13px; color: #333; }}
            tr:nth-child(even) {{ background-color: #f9f9f9; }}
            tr:hover {{ background-color: #f1f1f1; }}
            h2 {{ color: #004a99; border-bottom: 2px solid #004a99; padding-bottom: 10px; }}
            .nif {{ color: #666; font-size: 11px; }}
        </style>
    </head>
    <body>
        <h2>Lista de todas as empresas criadas nas últimas 24h em Portugal</h2>
        <p>Relatório automático gerado para Hugo Galaz.</p>
        <table>
            <tr>
                <th>Nome da empresa</th>
                <th>Nome do responsável</th>
                <th>Contactos</th>
                <th>Localidade</th>
                <th>Área de atividade</th>
            </tr>
    """
    
    if not companies:
        html += "<tr><td colspan='5' style='text-align: center;'>Nenhuma empresa nova detetada nas últimas 24h.</td></tr>"
    else:
        for c in companies:
            html += f"""
                <tr>
                    <td><b>{c['name']}</b><br><span class="nif">NIF: {c['nif']}</span></td>
                    <td>{c['responsible']}</td>
                    <td>{c['contacts']}</td>
                    <td>{c['location']}</td>
                    <td>{c['activity']}</td>
                </tr>
            """
        
    html += """
        </table>
        <br>
        <p><i>Este relatório é enviado diariamente às 6h (GMT/BST).</i></p>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(html, 'html'))
    
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(sender_email, password)
            server.send_message(msg)
        print("Email sent successfully!")
    except Exception as e:
        print(f"Error sending email: {e}")

async def main():
    print(f"Agent started at {datetime.now(pytz.timezone('Europe/Lisbon'))}")
    try:
        companies = await get_companies_from_einforma()
        print(f"Total companies extracted: {len(companies)}")
        send_email(companies)
    except Exception as e:
        print(f"Fatal error in agent execution: {e}")

if __name__ == "__main__":
    asyncio.run(main())
