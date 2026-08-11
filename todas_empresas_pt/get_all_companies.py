name: Base de Dados Incremental de Empresas

on:
  schedule:
    - cron: '0 6 * * *'   # 06:00 UTC = 07:00 Lisboa (inverno) / 06:00 Lisboa (verão, ajusta se quiseres precisão exata)
  workflow_dispatch:

permissions:
  contents: write   # necessário para o workflow poder fazer commit do CSV atualizado

jobs:
  scrape-and-store:
    runs-on: ubuntu-latest

    steps:
    - name: Checkout repository
      uses: actions/checkout@v4

    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: '3.12'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r todas_empresas_pt/requirements.txt
        playwright install --with-deps chromium

    - name: Run scraper and update database
      env:
        GMAIL_APP_PASSWORD: ${{ secrets.GMAIL_APP_PASSWORD }}
      run: |
        python todas_empresas_pt/get_all_companies.py

    - name: Commit updated database back to repo
      run: |
        git config user.name "github-actions[bot]"
        git config user.email "github-actions[bot]@users.noreply.github.com"
        git add todas_empresas_pt/empresas_db.csv
        git diff --staged --quiet || git commit -m "chore: atualizar base de empresas $(date -u +'%Y-%m-%d')"
        git push
if __name__ == "__main__":
    asyncio.run(main())
