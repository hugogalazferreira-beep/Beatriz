# Agente de Novas Empresas em Portugal

Este agente automatiza a recolha diária de novas empresas constituídas em Portugal e envia um relatório por email para `geral@hugogalaz.pt`.

## Como funciona

1. O script `main.py` utiliza Playwright para aceder ao portal `einforma.pt` e extrair a lista das últimas empresas criadas.
2. Filtra as empresas criadas nas últimas 24 horas.
3. Extrai detalhes como Nome, Localidade e Área de Atividade.
4. Envia um email formatado via Gmail.

## Configuração Necessária

Para que o agente consiga enviar emails através da sua conta Gmail (`hugo.galaz.ferreira@gmail.com`), é necessário configurar um **App Password**:

1. Vá às [definições de Segurança da sua Conta Google](https://myaccount.google.com/security).
2. Ative a **Verificação em dois passos** (se ainda não o fez).
3. Procure por **Palavras-passe de app** (App Passwords).
4. Crie uma nova palavra-passe com o nome "Agente Empresas".
5. Copie o código de 16 caracteres gerado.

### Configuração no GitHub

Este agente está configurado para correr no **GitHub Actions**. Para que funcione, deve adicionar o código copiado anteriormente como um "Secret":

1. No seu repositório GitHub, vá a **Settings** > **Secrets and variables** > **Actions**.
2. Clique em **New repository secret**.
3. Nome: `GMAIL_APP_PASSWORD`
4. Valor: (Cole aqui o código de 16 caracteres sem espaços)
5. Clique em **Add secret**.

O agente correrá automaticamente todos os dias às 6h (UTC).

## Ferramenta de Licenciamento (CLI)

O projeto inclui agora uma ferramenta para gerar e verificar chaves de licença baseadas no ID da máquina (MAC address).

### Como usar

1. **Gerar uma chave para a máquina atual:**
   ```bash
   python license_tool.py generate
   ```
   Isto exibirá o MAC address detetado e a chave de licença correspondente em blocos (ex: `GA3DU-MBQHJ-...`).

2. **Verificar uma chave:**
   ```bash
   python license_tool.py verify <CHAVE-AQUI>
   ```
   O script confirmará se a chave é válida para o hardware onde está a ser executado.

## Ficheiros do Projeto

- `main.py`: Lógica principal do agente.
- `license_tool.py`: Utilitário de geração e verificação de licenças.
- `.github/workflows/daily_agent.yml`: Configuração da automação diária.
- `requirements.txt`: Dependências do projeto.
