# Memória do escritório Cysar

Registro durável para consultar em sessões futuras. Sem segredos.

## Propósito

O repositório `cysar-office` (`/Users/dp/code/cysar/github/cysar-office`) é o ambiente de ferramentas de trabalho do escritório da Cysar. Os sistemas externos são ligados por MCPs diversos.

O README do repositório descreve o projeto como "Ambiente de escritório da Cysar".

## Convenções

- Conversas com o usuário neste projeto são em português.
- Fatos duráveis entram neste arquivo na mesma sessão em que são aprendidos.
- API keys, tokens e URLs com credencial não entram aqui nem em arquivo versionado.
- `.cursor/mcp.json` está no `.gitignore` porque a URL do EasyPanel contém a API key.

## MCPs

### EasyPanel

- Situação: habilitado no Cursor e testado com sucesso em 2026-09-29.
- Servidor: easypanel 2.36.0, transporte Streamable HTTP.
- Endereço do painel: `http://46.202.144.250:3000`.
- Configuração local: `.cursor/mcp.json` (não versionado). O endpoint segue `/api/mcp/<api-key>`.
- Namespace nesta sessão: `project-0-cysar-office-easypanel`.
- Projeto acessível: `cysar`, criado em 2026-09-29T19:41:05.408Z.
- Ferramentas estáveis: `search_procedures`, `execute_query`, `execute_mutation`, `execute_destructive`.
- Fluxo: buscar o procedimento com uma frase de ação e recurso; o resultado traz o `inputSchema`. Consultas usam `execute_query`. Mudanças não destrutivas usam `execute_mutation`. Operações que apagam, sobrescrevem, restauram, revogam ou interrompem recursos usam `execute_destructive`, e só com o alvo e a intenção confirmados.

### Google Calendar

- Situação em 2026-09-29: habilitado, autenticado e testado. Conta `pessoal`, e-mail `cysar@cysar.ai`, fuso `America/Fortaleza`. Calendário principal mais o de feriados do Brasil.
- Pacote: `@cocal/google-calendar-mcp`, transporte stdio, comando `/opt/homebrew/bin/npx`.
- Finalidade: controlar a agenda pessoal (listar, criar, atualizar, apagar eventos, responder convites e consultar disponibilidade).
- Credencial: arquivo `client_secret_*.json` em `.cursor/` (gitignored). Tipo `installed`, projeto `vital-effort-460219-h3`, redirect `http://localhost`.
- Tokens: `.cursor/google-calendar-tokens.json`.
- O JSON, os tokens e o `mcp.json` estão no `.gitignore`.
- Os `client_secret_*.json` em `~/Downloads` são clientes Web de outros sistemas e não entram neste MCP.

## Serviços no EasyPanel

### Odoo (`cysar` / `odoo`)

- Instalado em 2026-09-29 pelo template do EasyPanel. Imagem `odoo:latest` (Odoo 20.0-20260926) e banco `odoo-db` (`postgres:18`).
- Domínios: `cysar-odoo.nmmwv0.easypanel.host` e `crm-office.cysar.ai`, ambos na porta 8069.
- Em 2026-09-29 o HTTP escutava só em `127.0.0.1:8069` e os domínios respondiam 502. O comando de deploy ganhou `--http-interface=0.0.0.0` e o serviço foi republicado. Os dois domínios passaram a responder 200 em `/web/login`.
- MCP do Odoo: `@marcfargas/odoo-mcp` em stdio, credenciais no `.env` (gitignored). URL efetiva `https://crm-office.cysar.ai`, banco `odoo`. Habilitado e testado em 2026-09-29: empresa `Cysar`, e-mail `cysar@cysar.ai`, moeda BRL. O endpoint nativo `/mcp` responde 404 nesta imagem, então `ODOO_MCP_KEY` não entra na conexão.
- Módulo `cysar_brand` em `odoo/cysar_brand` e em `/mnt/extra-addons` no container. Instalado em 2026-09-29. Define `$o-community-color: #000000` antes do CSS do Odoo, trocando a marca `#71639e` por preto.
- Google Agenda no Odoo usa o cliente Web `odoo-cysar`. A URI de redirect aceita pelo Google é só `https://crm-office.cysar.ai/google_account/authentication`. O cliente Desktop do MCP da agenda pessoal é outro e não entra nessa tela.
- Em 2026-09-29 o Odoo via EasyPanel via o acesso como HTTP, e o Google recusava a URI. `proxy_mode` ficou ligado em `/etc/odoo/odoo.conf`. `web.base.url` ficou `https://crm-office.cysar.ai` com `web.base.url.freeze` = True. O módulo `cysar_proxy` em `odoo/cysar_proxy` força o esquema HTTPS na requisição, porque o proxy não entrega o protocolo certo. Depois disso a URL base vista pelo Odoo passou a ser `https://crm-office.cysar.ai/`.
- Ponto de restore do banco `odoo`, feito em 2026-09-29 antes de instalar contratos: provedor Local Disk, arquivo `cysar/odoo-db/restore-points/2026-09-29T23:35:59.734Z.sql.gz`. A restauração substitui o banco. Agendamento diário ficou desligado.
- Módulo OCA `contract` 19.0.1.0.6 adaptado e instalado como `20.0.1.0.6` em `/mnt/extra-addons/contract`. Licença AGPL-3. A branch 20.0 do repositório estava vazia. Assinaturas Enterprise não foi copiada. O comando de deploy do serviço voltou ao original.

## Histórico

- 2026-09-29: MCP do EasyPanel instalado no projeto, conexão testada e projeto `cysar` listado.
- 2026-09-29: Definido que o repositório receberá as ferramentas de trabalho do escritório, com vários MCPs.
- 2026-09-29: Memória durável criada neste arquivo e na regra `.cursor/rules/escritorio.mdc`.
- 2026-09-29: MCP do Google Calendar autenticado na conta `cysar@cysar.ai` (apelido `pessoal`) e testado com a listagem de eventos.
- 2026-09-29: Odoo republicado com `--http-interface=0.0.0.0`. Os domínios passaram a abrir a tela de login.
- 2026-09-29: Módulo `cysar_brand` instalado. A marca da interface passou de `#71639e` para `#000000`.
- 2026-09-29: Google Agenda do Odoo recusava o OAuth porque a URI saía em HTTP. `proxy_mode`, URL base HTTPS congelada e o módulo `cysar_proxy` passaram a fazer o Odoo enxergar `https://crm-office.cysar.ai/`. A sincronização foi confirmada pelo usuário no mesmo dia.
- 2026-09-29: Apps de Vendas instalados no Odoo (`sale`, `sale_management`, `sale_crm`, `l10n_br_sales`). Assinaturas permanece indisponível por ser Enterprise.
- 2026-09-29: Backup do banco `odoo` gravado em `cysar/odoo-db/restore-points/2026-09-29T23:35:59.734Z.sql.gz`. Em seguida o módulo OCA `contract` foi instalado (versão `20.0.1.0.6`, AGPL-3).
- 2026-09-29: Contrato `HP-2026-09-17` da Horizonte Piscinas (parceiro 22) lançado no Odoo. Implantação em duas parcelas de R$ 1.200 (17/09 quitada, 17/10 em aberto) e mensalidade de R$ 600 a partir de 17/11/2026.
- 2026-09-29: Projeto `Horizonte Piscinas — Agente SDR` criado para o mesmo contrato, com a tarefa de implantação e a tarefa recorrente de manutenção e sustentação.
- 2026-09-29: Solve Gestão e Negócios cadastrada como cliente (parceiro 24), com Francieli Bernardi como contato. Oportunidade na etapa Proposition, propostas apresentadas em 28/09/2026. Tarefa de retorno em 30/09/2026. Cotações S00001 Agenda MVP (R$ 3.000) e S00002 Projeto MVP (R$ 16.000), com os PDFs anexados.
- 2026-09-29: IVM Engenharia Ltda cadastrada como cliente (parceiro 25), com Marcelo Sábia como contato. Oportunidade Requisitos do IVM OS na etapa Proposition, proposta de 18/08/2026. Cotação S00003 de R$ 15.000, com o PDF anexado.
- 2026-09-29: Pousada Alphaville cadastrada como cliente (parceiro 27), com Fernando Macedo Carvalho como contato. Oportunidade Agente SDR na etapa New. A proposta ainda não foi criada.
- 2026-09-29: Skyller cadastrada como cliente (parceiro 29), com Adriano Fante como contato. Oportunidade Mentoria na etapa New.
- 2026-09-29: Hust cadastrada como cliente (parceiro 31), com Italo Tavares Lima como contato. Oportunidade Direção executiva na etapa Proposition, proposta de 01/09/2026. Cotação S00004 de R$ 15.000 mensais, com o PDF anexado.
- 2026-09-30: Marinho Creative Hub cadastrada como fornecedor (parceiro 33), com Nicollas Marinho como contato. Reunião confirmada na agenda Google em 01/10/2026, 19h–20h (`America/Fortaleza`). O calendário do Odoo ainda mostra 30/09, 19h.
- 2026-09-30: Agenda Google (`cysar@cysar.ai`) até 14/10 tinha duas reuniões: civilwork em 01/10, 10h–11h, e Marinho Creative Hub em 01/10, 19h–20h. Naquele momento o Odoo ainda listava a civilwork como 11h–12h e a Marinho como 30/09, 19h. O MCP da agenda não respondeu; a consulta foi feita na API com o token já gravado.
- 2026-10-01: Agenda do dia alinhada entre Google e Odoo: civilwork 10h–11h, vortex <> darley 15h–16h (só o organizador no convite, sem outro convidado) e Marinho Creative Hub 19h–20h. Sem atividade de CRM com prazo neste dia.
