# Portal do Consultor - Versão Premium

Esta é a Fase 4 do projeto Portal do Consultor, reconstruída com tecnologia de ponta para máxima performance, segurança e design premium.

## Stack Tecnológica

- **Backend:** FastAPI (Python 3.12)
- **Base de Dados:** SQLite com SQLAlchemy (Pronto para migrar para PostgreSQL)
- **Frontend:** HTML5, Tailwind CSS, JavaScript (Vanilla)
- **Design:** Modern Dark Mode, Glassmorphism, Tech Blue (#3b82f6)
- **Autenticação:** JWT (JSON Web Tokens) com armazenamento seguro em Cookies HTTPOnly

## Estrutura do Projeto

- `/app`: Lógica do backend (modelos, rotas, autenticação)
- `/static`: Ativos estáticos (imagens, CSS, JS)
- `/templates`: Páginas HTML processadas pelo Jinja2
- `main.py`: Ponto de entrada da aplicação
- `seed.py`: Script para inicializar dados de demonstração

## Como Executar

1. Instalar dependências:
   ```bash
   pip install -r requirements.txt
   ```

2. Inicializar a base de dados (Demo):
   ```bash
   python3 seed.py
   ```

3. Correr o servidor:
   ```bash
   python3 main.py
   ```

4. Aceder em `http://localhost:8000`

## Credenciais Demo

- **Consultor:** ana.silva / consultor2026
- **Admin:** admin / portaladmin2026

## Funcionalidades Implementadas (Fase 4)

- [x] Identidade Visual Premium (Logotipo e UI)
- [x] Autenticação Segura (Hashed Passwords)
- [x] Dashboard de Consultor com Gráficos
- [x] Registo de Vendas (API Funcional)
- [x] Painel de Administração para Gestão de Consultores
- [x] Sistema de Notificações (Simulação)
- [x] Suporte para Telecom (NOS, MEO, Vodafone, DIGI, NOWO) e Energia (EDP, Endesa, Galp, Iberdrola, Repsol, Plenitude)
