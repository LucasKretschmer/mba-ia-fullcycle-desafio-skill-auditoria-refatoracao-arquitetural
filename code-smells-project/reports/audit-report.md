================================
ARCHITECTURE AUDIT REPORT
================================
Project: code-smells-project
Stack:   Python + Flask 3.1.1
Files:   4 analyzed | ~780 lines of code
Date:    2026-10-05

## Summary
CRITICAL: 6 | HIGH: 5 | MEDIUM: 5 | LOW: 5

## Findings

### #1 [CRITICAL] Credenciais / segredos hardcoded (AP01)
File: app.py:7
controllers.py:289
database.py:76-78
Description: `app.config["SECRET_KEY"] = "minha-chave-super-secreta-123"` fixo no código e repetido literalmente na resposta de `health_check` (`"secret_key": "minha-chave-super-secreta-123"`). O seed de `get_db` grava credenciais reais de usuários (`("Admin", "admin@loja.com", "admin123", "admin")`).
Impact: Qualquer pessoa com acesso ao repositório (ou a `GET /health`) obtém a chave que assina sessões/cookies do Flask e a senha do administrador; impossível ter valores diferentes por ambiente.
Recommendation: Ler `SECRET_KEY` de variável de ambiente em um módulo `config`, com fallback apenas para desenvolvimento, documentar em `.env.example` e remover o segredo da resposta do health (Playbook T1).

### #2 [CRITICAL] SQL Injection (AP02)
File: models.py:28, 48-49, 58-60, 68, 92, 110, 127-128, 140, 149-150, 155, 158-160, 164-165, 174, 188, 192, 220, 224, 280, 291-297
app.py:62-69
Description: Todas as queries de `models.py` são montadas por concatenação, ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` em `login_usuario` e `" AND (nome LIKE '%" + termo + "%' OR descricao LIKE '%" + termo + "%')"` em `buscar_produtos`. Em `app.py`, `executar_query` faz `cursor.execute(query)` com o SQL recebido em `dados.get("sql")`.
Impact: Um e-mail `' OR '1'='1' --` autentica sem senha; `GET /produtos/busca?q=` permite ler/alterar qualquer tabela; `POST /admin/query` executa SQL arbitrário (incluindo `DROP TABLE`).
Recommendation: Usar placeholders `?` com tupla de parâmetros em todas as queries e remover o endpoint de SQL arbitrário (Playbook T2).

### #3 [CRITICAL] God Class / God File (AP03)
File: models.py:1-314
app.py:6-88
controllers.py:1-292
Description: `models.py` (314 linhas) concentra acesso a dados e regras de quatro domínios (produtos, usuários, pedidos e relatório com cálculo de desconto em `relatorio_vendas`). `app.py` mistura configuração (`SECRET_KEY`, `DEBUG`, `CORS`), registro de todas as rotas, SQL direto nas rotas `/admin/*` e boot do servidor. `controllers.py` reúne handlers de todos os domínios com validação, notificações e acesso ao banco.
Impact: Impossível testar um domínio isoladamente; qualquer mudança de schema ou regra afeta arquivos que tratam de tudo; alto risco de regressão.
Recommendation: Separar em `config`, `models/` por entidade, `controllers/` por domínio, `routes/` (views) por blueprint e `app.py` como factory/entry point (Playbook T3).

### #4 [CRITICAL] Endpoint sensível sem autenticação/autorização (AP04)
File: app.py:47-57, 59-78
Description: `POST /admin/reset-db` (`reset_database`) apaga `itens_pedido`, `pedidos`, `produtos` e `usuarios`, e `POST /admin/query` (`executar_query`) executa SQL enviado pelo cliente; nenhum dos dois tem qualquer verificação de identidade ou papel. O `login` (controllers.py:176-180) não emite credencial verificável, então não existe mecanismo de autorização no sistema.
Impact: Qualquer cliente da rede apaga toda a base ou extrai/altera dados com uma única requisição.
Recommendation: Remover o executor de SQL arbitrário e proteger `/admin/reset-db` com token administrativo vindo de variável de ambiente (desabilitado quando não configurado) via decorator (Playbook T13).

### #5 [CRITICAL] Armazenamento inseguro de senha (AP05)
File: models.py:110, 127-128
database.py:76-78
Description: `criar_usuario` grava `senha` exatamente como recebida (`"... VALUES ('" + nome + "', '" + email + "', '" + senha + "' ..."`); `login_usuario` compara a senha dentro da query (`AND senha = '" + senha + "'`); o seed insere `"admin123"`, `"123456"`, `"senha123"` em texto puro.
Impact: Vazamento do banco (ou de `GET /usuarios`, ver #6) entrega as senhas reais dos clientes, reutilizáveis em outros serviços.
Recommendation: Gerar hash com `werkzeug.security.generate_password_hash` ao criar/seedar e verificar com `check_password_hash` após buscar o usuário pelo e-mail (Playbook T5).

### #6 [CRITICAL] Exposição de dados sensíveis (AP06)
File: models.py:83, 99
controllers.py:285-289
controllers.py:161, 179, 182
Description: `get_todos_usuarios` e `get_usuario_por_id` serializam `"senha": row["senha"]`, devolvida por `GET /usuarios` e `GET /usuarios/<id>`. `health_check` retorna `"db_path": "loja.db"`, `"debug": True` e `"secret_key"`. E-mails de usuários são logados em `print("Login falhou: " + email)` e similares. Além disso, todos os handlers devolvem `str(e)` ao cliente (detalhado em #14).
Impact: Endpoints públicos entregam senhas de todos os usuários e a chave secreta da aplicação; logs acumulam PII.
Recommendation: Remover `senha` da serialização de usuário, tirar config/segredo do health check e trocar `print` por logger sem PII (Playbook T5, T14).

### #7 [HIGH] Regra de negócio no controller/rota (Fat Controller) (AP07)
File: controllers.py:266-274
app.py:49-55, 66-76
controllers.py:208-210, 247-250
controllers.py:28-54, 72-90
Description: `health_check` abre cursor e executa `SELECT COUNT(*)` direto no handler; as rotas `/admin/*` em `app.py` usam `get_db().cursor()` sem passar por model. Efeitos colaterais de negócio ficam inline no handler (`print("ENVIANDO EMAIL: Pedido ...")`, `print("NOTIFICAÇÃO: Pedido ... cancelado. Devolver estoque.")`). `criar_produto` (39 linhas) e `atualizar_produto` contêm toda a regra de validação de produto.
Impact: Regras não reutilizáveis nem testáveis sem HTTP; trocar o canal de notificação exige editar controllers.
Recommendation: Mover acesso a dados para models, regras/notificações para services e deixar o controller só traduzindo request/response (Playbook T6).

### #8 [HIGH] Acoplamento forte sem injeção de dependência (AP08)
File: models.py:5, 25, 44, 55, 66, 73, 90, 106, 123, 134, 172, 204, 236, 276, 286
controllers.py:3, 266
app.py:4, 49, 66, 82
Description: Todas as funções de dados chamam o `get_db()` global importado de `database`, e controllers/rotas também importam e usam a conexão concreta diretamente.
Impact: Impossível trocar o banco ou usar um banco de teste sem monkeypatch; camadas acopladas à implementação concreta do SQLite.
Recommendation: Obter a conexão por um ponto único ligado ao contexto da aplicação (`flask.g` + `teardown_appcontext`), com caminho do banco vindo da config da app (Playbook T7).

### #9 [HIGH] Estado global mutável (AP09)
File: database.py:4, 8-10
Description: `db_connection = None` em nível de módulo, alterado via `global db_connection` em `get_db`, com `sqlite3.connect(db_path, check_same_thread=False)` compartilhado entre todas as threads/requisições.
Impact: Requisições concorrentes compartilham o mesmo cursor/transação: um `commit` de uma requisição efetiva escritas parciais de outra; condições de corrida no estoque.
Recommendation: Uma conexão por requisição em `flask.g`, fechada no teardown (Playbook T7).

### #10 [HIGH] Operação multi-etapa sem transação (AP10)
File: models.py:133-169
app.py:51-55
Description: `criar_pedido` lê estoque (138-146), insere o pedido (148-152) e, em loop, insere `itens_pedido` e decrementa `estoque` (154-166), com um único `db.commit()` na linha 168 e nenhum `rollback`. Uma exceção no meio (ex.: item sem `quantidade`) deixa a transação aberta na conexão global, que será efetivada pelo próximo `commit` de outra requisição. `reset_database` faz quatro `DELETE` sem tratamento de falha.
Impact: Pedidos sem itens, estoque decrementado sem pedido e inconsistência de dados sob erro ou concorrência.
Recommendation: Envolver o fluxo em transação explícita (`with conn:` / commit-rollback) dentro do service/model (Playbook T9).

### #11 [HIGH] Configuração insegura de execução (AP11)
File: app.py:8, 9, 88
database.py:5
controllers.py:286-288
Description: `app.config["DEBUG"] = True` e `app.run(host="0.0.0.0", port=5000, debug=True)` expõem o debugger interativo do Werkzeug na rede; `CORS(app)` libera qualquer origem; porta, `db_path = "loja.db"` e `"ambiente": "producao"` estão fixos no código.
Impact: O debugger permite execução remota de código; qualquer site pode chamar a API pelo navegador da vítima; impossível configurar por ambiente.
Recommendation: Ler `DEBUG`, `HOST`, `PORT`, `DATABASE_PATH` e origens de CORS de variáveis de ambiente com defaults seguros (Playbook T1).

### #12 [MEDIUM] Queries N+1 (AP12)
File: models.py:187-193, 219-225
models.py:140, 155
models.py:239-254
controllers.py:269-274
Description: `get_pedidos_usuario` e `get_todos_pedidos` executam `SELECT * FROM itens_pedido WHERE pedido_id = ...` por pedido e `SELECT nome FROM produtos WHERE id = ...` por item (`cursor2`/`cursor3`). `criar_pedido` consulta o mesmo produto duas vezes por item. `relatorio_vendas` faz cinco queries separadas (`COUNT`, `SUM`, três `COUNT ... WHERE status`) e `health_check` mais três `COUNT(*)`.
Impact: `GET /pedidos` cresce para 1 + P + I queries; degrada linearmente com o volume de pedidos.
Recommendation: Buscar itens com `JOIN` em uma única query agrupando em memória e consolidar o relatório em uma query agregada (`SUM(CASE WHEN ...)`) (Playbook T8).

### #13 [MEDIUM] Validação ausente, fraca ou duplicada (AP13)
File: controllers.py:28-50, 72-90
controllers.py:43, 45, 87, 89
controllers.py:119, 121
controllers.py:169-170, 239-240
controllers.py:153-158
controllers.py:195-201
Description: O bloco de validação de produto é copiado entre `criar_produto` e `atualizar_produto`, mas a atualização omite as regras de tamanho do nome e de categoria. `preco < 0` é avaliado sem checar tipo (string → `TypeError` → 500). `float(preco_min)` com valor inválido → `ValueError` → 500. `login` e `atualizar_status_pedido` chamam `dados.get(...)` sem checar se o corpo é JSON (None → 500). `criar_usuario` não valida formato nem unicidade de e-mail. `criar_pedido` não valida `produto_id`/`quantidade` dos itens: item sem chave gera `KeyError` (500) e `quantidade` negativa passa na checagem de estoque e aumenta o estoque. `atualizar_status_pedido` retorna 200 para pedido inexistente.
Impact: Entradas inválidas viram 500 ou corrompem dados (estoque negativo/inflado, usuários duplicados).
Recommendation: Centralizar validação por entidade em funções de validação reutilizadas por criar/atualizar, levantando erro de validação tratado como 400 (Playbook T10).

### #14 [MEDIUM] Error handling inconsistente / vazamento de exceção (AP14)
File: controllers.py:10-12, 21-22, 60-62, 95-96, 108-109, 125-126, 133-134, 143-144, 164-165, 185-186, 218-220, 226-227, 234-235, 254-255, 261-262, 291-292
app.py:77-78
models.py:143, 145
Description: Cada handler repete `except Exception as e: return jsonify({"erro": str(e)}), 500`; não há `@app.errorhandler`. Formatos de erro divergem (`{"erro"}`, `{"erro", "sucesso": False}`, `{"status": "erro", "detalhes"}`). O model sinaliza erro de negócio retornando dict `{"erro": ...}` em vez de exceção.
Impact: Mensagens internas (SQL, paths) chegam ao cliente; duplicação de 17 blocos idênticos; contrato de erro imprevisível.
Recommendation: Exceções de domínio (`NotFoundError`, `ValidationError`) e error handler central que devolve JSON padronizado e loga o 500 sem expor detalhes (Playbook T4).

### #15 [MEDIUM] Código duplicado (AP15)
File: models.py:12-21, 31-40, 304-313
models.py:79-86, 95-102
models.py:171-201, 203-233
Description: O dicionário de produto (`"id": row["id"], "nome": row["nome"], ...`) é montado manualmente três vezes, o de usuário duas vezes; `get_pedidos_usuario` e `get_todos_pedidos` são idênticas exceto pelo `WHERE usuario_id`.
Impact: Adicionar um campo exige editar vários pontos; correções (como remover `senha`) podem ser esquecidas em um deles.
Recommendation: Funções `produto_para_dict`/`usuario_para_dict` únicas e uma consulta de pedidos parametrizada por filtro opcional (Playbook T6, T10).

### #16 [MEDIUM] Integridade referencial ignorada (AP17)
File: models.py:65-70
database.py:36-53
models.py:196, 228
models.py:148-150
Description: `deletar_produto` executa `DELETE FROM produtos` mesmo com `itens_pedido` referenciando o produto; as tabelas `pedidos` e `itens_pedido` não declaram `FOREIGN KEY`; o fallback `"produto_nome": ... else "Desconhecido"` admite a existência de órfãos; `criar_pedido` insere pedido para `usuario_id` sem verificar se o usuário existe.
Impact: Histórico de pedidos perde referência do produto; pedidos de usuários inexistentes contaminam relatórios.
Recommendation: Declarar `FOREIGN KEY` no schema, verificar existência do usuário antes de criar o pedido e tratar exclusão de produto referenciado (Playbook T9).

### #17 [LOW] Magic numbers / strings (AP18)
File: models.py:257-262
controllers.py:52, 242
controllers.py:47, 49
models.py:150, 247, 250, 253
app.py:36
controllers.py:285
Description: Faixas de desconto (`10000`/`0.1`, `5000`/`0.05`, `1000`/`0.02`), lista de categorias e lista de status literais no handler, limites de nome `2`/`200`, status `'pendente'`/`'aprovado'`/`'cancelado'` repetidos em SQL, versão `"1.0.0"` duplicada.
Impact: Regras de negócio escondidas em literais; mudar uma faixa ou um status exige caçar ocorrências.
Recommendation: Constantes nomeadas em um módulo de domínio (`CATEGORIAS_VALIDAS`, `STATUS_VALIDOS`, `FAIXAS_DESCONTO`, `VERSAO_API`) (Playbook T12).

### #18 [LOW] Nomes ruins (AP19)
File: controllers.py:14, 56, 64, 98, 136, 160
models.py:24, 54, 65, 89
models.py:187, 191, 193, 219, 223, 225
Description: Parâmetro/variável `id` sombreando o builtin (`def buscar_produto(id)`, `id = models.criar_produto(...)`); cursores numerados `cursor2`, `cursor3` e abreviação `prod`.
Impact: Leitura mais difícil e risco de bug ao usar o builtin `id` no mesmo escopo.
Recommendation: Renomear para `produto_id`, `usuario_id`, `novo_id`, e eliminar os cursores extras com o JOIN de #12 (Playbook T12).

### #19 [LOW] Código morto (AP20)
File: database.py:2
models.py:2
controllers.py:268
Description: `import os` e `import sqlite3` nunca usados; `cursor.execute("SELECT 1")` em `health_check` sem leitura do resultado, seguido de outras queries que já provam a conexão.
Impact: Ruído e falsa impressão de dependências.
Recommendation: Remover imports e instruções sem efeito (Playbook T12).

### #20 [LOW] `print` no lugar de logger (AP21)
File: controllers.py:8, 11, 57, 61, 106, 161, 179, 182, 208-210, 219, 248, 250
app.py:56, 83-86
Description: Eventos e erros registrados com `print(...)`, incluindo simulação de envio (`print("ENVIANDO SMS: Seu pedido foi recebido!")`) e banner de boot `print("SERVIDOR INICIADO")`.
Impact: Sem nível, timestamp ou destino configurável; impossível filtrar em produção.
Recommendation: `logging.getLogger(__name__)` com nível adequado e notificações isoladas em um service (Playbook T14).

### #21 [LOW] Condicionais verbosas (AP22)
File: controllers.py:200
models.py:244-245
models.py:63, 70, 283
Description: `if not itens or len(itens) == 0` (a segunda condição é redundante), `if faturamento is None: faturamento = 0` em vez de `or 0`/`COALESCE`, e funções que sempre fazem `return True` sem que o retorno seja usado.
Impact: Ruído de leitura e retornos que sugerem um sinal de falha inexistente.
Recommendation: Simplificar as expressões e remover retornos constantes (Playbook T12).

## Deprecated APIs
Nenhuma API deprecated encontrada. O projeto usa `sqlite3` da biblioteca padrão e apenas APIs atuais do Flask 3.1 (`app.add_url_rule`, `jsonify`, `request.get_json`); não há `utcnow`, `Model.query.get`, `before_first_request` nem `flask.__version__`.

## Architecture Notes
Projeto monolítico em quatro arquivos planos: `app.py` acumula config, rotas e SQL; `models.py` é um God File com dados e regras de todos os domínios; `database.py` mistura conexão global, schema e seed. A refatoração criará `config.py`, `database.py` com conexão por requisição, `models/` por entidade (SQL parametrizado e serialização única), `services/` para regras (pedido transacional, relatório, notificações), `controllers/` finos, `routes/` como views/blueprints e um error handler central. Serão preservados os paths, métodos, status codes, chaves de resposta, o seed inicial e o comando `python app.py`.

================================
Total: 21 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
