================================
ARCHITECTURE AUDIT REPORT
================================
Project: task-manager-api
Stack:   Python 3 + Flask 3.0.0 (Flask-SQLAlchemy 3.1.1)
Files:   15 analyzed | ~1158 lines of code
Date:    2026-10-05

## Summary
CRITICAL: 4 | HIGH: 4 | MEDIUM: 8 | LOW: 5

## Findings

### #1 [CRITICAL] Credenciais / segredos hardcoded (AP01)
File: app.py:13
services/notification_service.py:7-10
Description: `app.config['SECRET_KEY'] = 'super-secret-key-123'` fixo no entry point e credenciais SMTP literais no construtor de `NotificationService`: `self.email_user = 'taskmanager@gmail.com'`, `self.email_password = 'senha123'` (host `smtp.gmail.com` e porta `587` também fixos).
Impact: Qualquer pessoa com acesso ao repositório obtém a chave de assinatura de sessão do Flask e a senha da conta de e-mail; impossível ter valores diferentes por ambiente ou rotacionar sem novo deploy.
Recommendation: Mover `SECRET_KEY` e credenciais SMTP para variáveis de ambiente lidas em `config/settings.py`, com fallback apenas para desenvolvimento, e documentar em `.env.example` (Playbook T1).

### #2 [CRITICAL] Endpoint sensível sem autenticação/autorização (AP04)
File: routes/user_routes.py:52, 71, 119-122, 135-151, 210
routes/report_routes.py:211-223
routes/task_routes.py:225-238
Description: Nenhuma rota tem verificação de identidade. `login` devolve um token previsível e não verificável: `'token': 'fake-jwt-token-' + str(user.id)`. `create_user` aceita `role` do cliente (`data.get('role', 'user')`, inclusive `'admin'`) e `update_user` permite trocar `role` de qualquer usuário (escalada de privilégio). `DELETE /users/<id>`, `DELETE /tasks/<id>` e `DELETE /categories/<id>` são acessíveis a qualquer um.
Impact: Qualquer cliente anônimo cria um admin, promove a si mesmo, apaga usuários (com todas as tasks) e categorias; o "token" pode ser forjado trocando o número do id.
Recommendation: Gerar token assinado no login (stdlib `hmac`/`itsdangerous` do Flask com `SECRET_KEY`), criar decorator `require_auth`/`require_admin` em `middlewares/` e aplicá-lo às rotas destrutivas e à atribuição de `role` (Playbook T13).

### #3 [CRITICAL] Armazenamento inseguro de senha (AP05)
File: models/user.py:29, 32
routes/user_routes.py:64, 115
seed.py:19, 26, 33
Description: `set_password` grava `hashlib.md5(pwd.encode()).hexdigest()` e `check_password` compara MD5 sem salt. A política aceita senhas de 4 caracteres (`len(password) < 4`) e o seed cria usuários com `'1234'`, `'abcd'`, `'pass'`.
Impact: MD5 sem salt é revertido por rainbow table em segundos; um vazamento do `tasks.db` (ou da resposta da API, ver #4) expõe as senhas reais de todos os usuários.
Recommendation: Usar `werkzeug.security.generate_password_hash`/`check_password_hash` (já vem com o Flask) e aplicar comprimento mínimo via constante (Playbook T5).

### #4 [CRITICAL] Exposição de dados sensíveis (AP06)
File: models/user.py:16-25
routes/user_routes.py:33, 85, 129, 209
Description: `User.to_dict()` inclui `'password': self.password` e é devolvido em `GET /users/<id>` (`data = user.to_dict()`), `POST /users`, `PUT /users/<id>` e até na resposta de `POST /login` (`'user': user.to_dict()`).
Impact: O hash MD5 de qualquer usuário é obtido com um GET anônimo e, combinado com #3, a senha em texto puro é recuperada trivialmente.
Recommendation: Remover `password` da serialização pública do model e garantir que nenhuma view devolva o campo (Playbook T5, T14).

### #5 [HIGH] God Class / God File (AP03)
File: routes/report_routes.py:1-223
Description: O blueprint `report_bp` mistura dois domínios (relatórios `summary_report`/`user_report` e o CRUD completo de categorias `get_categories`..`delete_category`), acessa o ORM direto, contém as regras de agregação e monta a resposta à mão. `summary_report` (linhas 13-101) tem 89 linhas com 15 queries e loops de agregação. Severidade reduzida de CRITICAL para HIGH porque o arquivo não abre conexão nem guarda config, e o projeto já tem `models/` separados.
Impact: Mudar qualquer regra de categoria obriga a mexer no arquivo de relatórios; a lógica de relatório não pode ser testada sem HTTP e banco reais.
Recommendation: Separar em `routes/category_routes.py` + `controllers/category_controller.py` e `controllers/report_controller.py`, levando os cálculos para `services/report_service.py` (Playbook T3).

### #6 [HIGH] Regra de negócio no controller/rota (Fat Controller) (AP07)
File: routes/task_routes.py:12-63, 86-154, 157-223, 241-271, 274-299
routes/user_routes.py:43-90, 93-132, 135-151
routes/report_routes.py:104-155, 168-188
Description: Os handlers concentram validação, regra de domínio e acesso ao ORM: `create_task` (69 linhas) valida título/status/prioridade, checa existência de `User`/`Category`, converte data e tags e faz `db.session.add/commit`; `update_task` repete o fluxo; `delete_user` faz a cascata manual de tasks (`for t in tasks: db.session.delete(t)`); `user_report` calcula estatísticas em loop. Toda rota usa `Model.query...`/`db.session...` diretamente.
Impact: Regras não podem ser reutilizadas nem testadas sem o contexto HTTP; qualquer mudança de regra exige editar várias rotas.
Recommendation: Rotas finas que apenas registram URL → controllers que leem request e devolvem resposta → services com validação e regras, usando os models (Playbook T6).

### #7 [HIGH] Acoplamento forte sem injeção de dependência (AP08)
File: app.py:9-31
seed.py:2
services/notification_service.py:5-10, 15
Description: Não há application factory: `app = Flask(__name__)`, a config e `db.create_all()` (linhas 30-31) rodam no import do módulo. `seed.py` faz `from app import app, db`, acoplando o script ao objeto global da aplicação. `NotificationService` instancia `smtplib.SMTP(self.email_host, self.email_port)` internamente com host fixo.
Impact: Impossível criar uma app com outra config (teste, banco em memória) sem monkeypatch; importar `app` cria tabelas como efeito colateral; o serviço de e-mail não pode ser substituído por um fake.
Recommendation: Criar `create_app(config)` em `app.py`, mover init de extensões e `create_all` para a factory, fazer o seed chamar a factory e receber host/credenciais do serviço via config (Playbook T7).

### #8 [HIGH] Configuração insegura de execução (AP11)
File: app.py:11, 15, 34
Description: `app.run(debug=True, host='0.0.0.0', port=5000)` expõe o debugger interativo do Werkzeug em todas as interfaces; `CORS(app)` libera qualquer origem; `SQLALCHEMY_DATABASE_URI = 'sqlite:///tasks.db'` e porta são fixos no código.
Impact: O debugger permite execução remota de código se a app subir em rede; qualquer site pode chamar a API pelo navegador do usuário; não dá para trocar banco/porta por ambiente.
Recommendation: Ler `DEBUG`, `HOST`, `PORT`, `DATABASE_URL` e `CORS_ORIGINS` de variáveis de ambiente em `config/settings.py`, com `DEBUG` desligado por padrão (Playbook T1).

### #9 [MEDIUM] Estado global mutável (AP09)
File: services/notification_service.py:6, 31-36, 43-48
Description: `self.notifications = []` é usado como "banco" em memória (`self.notifications.append({...})` em `notify_task_assigned` e leitura em `get_notifications`). Severidade reduzida de HIGH para MEDIUM porque a classe não é instanciada em nenhum lugar do projeto (ver #19).
Impact: Se for ligado, as notificações somem a cada restart e divergem entre workers/processos.
Recommendation: Como o serviço não é usado, remover o estado em memória junto com o código morto; se for mantido, persistir em tabela e injetar dependências (Playbook T7).

### #10 [MEDIUM] Queries N+1 (AP12)
File: routes/task_routes.py:42, 51, 275-279
routes/user_routes.py:22
routes/report_routes.py:15-28, 56, 163
Description: `get_tasks` faz `User.query.get(t.user_id)` e `Category.query.get(t.category_id)` dentro do loop de tasks; `get_users` usa `len(u.tasks)` com lazy loading por usuário; `summary_report` roda `Task.query.filter_by(user_id=u.id).all()` por usuário e 12 `COUNT` separados por status/prioridade; `get_categories` faz `Task.query.filter_by(category_id=c.id).count()` por categoria; `task_stats` faz 5 `COUNT` separados.
Impact: Número de queries cresce linearmente com tasks/usuários/categorias (`GET /tasks` chega a 1 + 2N queries para N tasks), degradando latência.
Recommendation: Usar os relationships com `joinedload`/`selectinload` e agregações `GROUP BY` (`func.count` agrupado por `status`, `priority`, `user_id`, `category_id`) na camada de service (Playbook T8).

### #11 [MEDIUM] Validação ausente, fraca ou duplicada (AP13)
File: routes/task_routes.py:96-114, 166-184, 261, 264
routes/user_routes.py:61, 102-103, 106, 124-125
routes/report_routes.py:196-202
utils/helpers.py:21, 52-55, 57-108
models/task.py:38-48
Description: `priority < 1` compara sem converter (`"priority": "2"` gera `TypeError` → 500 HTML); `len(title)` quebra se `title` não for string; `int(priority)`/`int(user_id)` em `search_tasks` sem tratamento (`?priority=abc` → 500); `update_category` faz `'name' in data` sem checar `data` (body vazio → 500) e aceita `color` sem `is_valid_color`; `update_user` aceita `name` vazio e `active` de qualquer tipo. O bloco de validação de task é copiado entre `create_task` e `update_task`, a regex de e-mail aparece 3 vezes, e `process_task_data`, `validate_email`, `is_valid_color`, `Task.validate_status`/`validate_priority` existem mas nenhuma rota os usa.
Impact: Payloads simples derrubam endpoints com 500 em vez de 400; regras divergem entre criação e atualização.
Recommendation: Centralizar validação em um módulo de validators/services único (reaproveitando `process_task_data`), convertendo tipos e levantando `ValidationError` tratada pelo handler central (Playbook T10).

### #12 [MEDIUM] Error handling inconsistente / vazamento de exceção (AP14)
File: routes/task_routes.py:62, 137, 151, 204, 221, 236
routes/user_routes.py:87, 130, 149
routes/report_routes.py:186, 207, 221
utils/helpers.py:46, 49, 88
app.py:1-34
Description: 12 `except:` sem tipo (bare except) engolem qualquer erro; `get_tasks` envolve o handler inteiro em `try/except` e devolve `{'error': 'Erro interno'}` sem registrar nada; o mesmo bloco `try: commit / except: rollback; return 500` é repetido em cada handler. Não existe `@app.errorhandler`: erros não tratados (ver #11) e rotas inexistentes devolvem HTML padrão do Flask, enquanto o resto da API devolve JSON `{'error': ...}`.
Impact: Falhas reais ficam invisíveis; o cliente recebe formatos diferentes de erro conforme o caminho.
Recommendation: Criar exceções de domínio (`NotFoundError`, `ValidationError`, `ConflictError`) e registrar handlers centrais JSON para elas, para `HTTPException` e para `Exception` (com log), removendo os try/except repetidos (Playbook T4).

### #13 [MEDIUM] Código duplicado (AP15)
File: routes/task_routes.py:17-39, 71-80, 284-287, 289-297
routes/user_routes.py:15-23, 162-180
routes/report_routes.py:19-22, 33-36, 67, 132-135, 151
models/task.py:50-60
utils/helpers.py:14-17
Description: A regra "task atrasada" (`due_date < datetime.utcnow()` e status diferente de `done`/`cancelled`) é reimplementada em 6 lugares, embora `Task.is_overdue()` já exista. A serialização de task é montada à mão em `get_tasks` e `get_user_tasks` em vez de `to_dict()`; os contadores por status de `task_stats` repetem os de `summary_report`; o cálculo `round((done / total) * 100, 2) if total > 0 else 0` aparece 3 vezes, mas `calculate_percentage` já existe.
Impact: Uma mudança de regra (ex.: novo status final) precisa ser feita em 6 lugares e é fácil esquecer um.
Recommendation: Usar `Task.is_overdue()`/`to_dict()` como fonte única e mover estatísticas para um service compartilhado entre `/tasks/stats` e `/reports/summary` (Playbook T6, T10).

### #14 [MEDIUM] Uso de APIs deprecated: `Query.get()` (AP16)
File: routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227
routes/user_routes.py:29, 94, 136, 155
routes/report_routes.py:105, 192, 213
Description: 16 chamadas a `Model.query.get(id)` (ex.: `task = Task.query.get(task_id)`), API legada no SQLAlchemy 2.x (instalado 2.1.3) que emite `LegacyAPIWarning`.
Impact: Warnings em runtime e quebra garantida quando a legacy Query API for removida.
Recommendation: Trocar por `db.session.get(Model, id)` e consultas novas por `db.select(...)` (Playbook T11).

### #15 [MEDIUM] Uso de APIs deprecated: `datetime.utcnow()` (AP16)
File: models/task.py:15, 16, 52
models/user.py:14
models/category.py:11
routes/task_routes.py:31, 72, 215, 285
routes/user_routes.py:172
routes/report_routes.py:35, 42, 45, 71, 133
services/notification_service.py:35
utils/helpers.py:38
seed.py:66, 67, 69, 70, 74
Description: `datetime.utcnow` usado como default de colunas (`default=datetime.utcnow`) e em todas as comparações de prazo; deprecated desde o Python 3.12 (ambiente roda 3.12.3).
Impact: `DeprecationWarning` em cada chamada e remoção futura; datetimes naive dificultam comparação correta de fuso.
Recommendation: Centralizar um helper `utcnow()` baseado em `datetime.now(timezone.utc)` (mantendo valor naive para compatibilidade com as colunas SQLite existentes) e usá-lo em todos os pontos (Playbook T11).

### #16 [MEDIUM] Integridade referencial ignorada (AP17)
File: routes/report_routes.py:211-223
routes/user_routes.py:140-142
models/task.py:13-14, 20-21
Description: `delete_user` resolve a cascata manualmente na rota (`for t in tasks: db.session.delete(t)`); as FKs `db.ForeignKey('users.id')`/`('categories.id')` e os `relationship(..., backref='tasks')` não declaram `ondelete`/`cascade`, e o SQLite não aplica FK por padrão. Em `delete_category` a integridade só é mantida implicitamente: o default do ORM zera `category_id` das tasks carregadas via backref (correção pós-baseline: a versão inicial deste relatório afirmava que o `category_id` ficava órfão; o baseline da Fase 3 mostrou `category_id: null` após o delete).
Impact: A política de exclusão não está declarada em lugar nenhum: depende de um loop na rota (usuários) e de um comportamento default do ORM (categorias); qualquer delete fora desses caminhos (SQL direto, bulk delete) deixa registros órfãos.
Recommendation: Declarar a política no model (cascade nas tasks do usuário, desvincular `category_id` ao apagar categoria) e executá-la no service dentro da mesma transação (Playbook T9).

### #17 [LOW] Magic numbers / strings (AP18)
File: routes/task_routes.py:96, 99, 110, 113, 136, 167, 169, 177, 182, 203
routes/user_routes.py:64, 71, 115, 120
routes/report_routes.py:45, 84-88, 129
models/task.py:39, 46
utils/helpers.py:75, 110-116
Description: Lista de status `['pending', 'in_progress', 'done', 'cancelled']` repetida 5 vezes, roles `['user', 'admin', 'manager']` 3 vezes, limites de título `3`/`200`, prioridade `1..5`, senha `4`, formato `'%Y-%m-%d'`, janela de `7` dias e `t.priority <= 2` como "alta prioridade" literais. As constantes `VALID_STATUSES`, `VALID_ROLES`, `MAX_TITLE_LENGTH` etc. existem em `utils/helpers.py:110-116` mas não são usadas.
Impact: Alterar uma regra exige caçar literais espalhados; divergência fácil entre rotas.
Recommendation: Centralizar em constantes do domínio (ex.: `models/constants.py` ou no próprio model) e usá-las em validators e services (Playbook T12).

### #18 [LOW] Nomes ruins / pouco descritivos (AP19)
File: routes/report_routes.py:10, 24-28, 157-223
routes/task_routes.py:16, 51
routes/user_routes.py:14
models/user.py:27, 31
seed.py:16-61, 78-79
Description: Variáveis de uma letra fora de loops curtos (`p1`..`p5`, `u`, `t`, `c`, `td`, `cat`, `d`), parâmetro `pwd` em `set_password`/`check_password`, e `report_bp`/`report_routes.py` hospedando o CRUD de categorias (nome enganoso).
Impact: Leitura e busca no código ficam mais lentas; quem procura categorias não acha no arquivo esperado.
Recommendation: Renomear para nomes de domínio (`priority_counts`, `task`, `category`, `password`) e mover categorias para módulo próprio (Playbook T12).

### #19 [LOW] Imports, variáveis e código mortos (AP20)
File: app.py:7
routes/task_routes.py:7, 221
routes/user_routes.py:6
routes/report_routes.py:7, 8
models/task.py:3
utils/helpers.py:3-7, 9-12, 19-41, 52-55, 57-108, 110-116
models/task.py:38-60
models/user.py:34-38
services/notification_service.py:1-48
requirements.txt:4-6
Description: Imports não usados: `os, sys, json` (app.py), `json, os, sys, time` (task_routes.py), `hashlib, json` (user_routes.py), `format_date, calculate_percentage, json` (report_routes.py), `json` (models/task.py), `os, json, sys, math, hashlib` (helpers.py); variável `e` não usada em `update_task`. Funções nunca chamadas: `format_date`, `validate_email`, `sanitize_string`, `generate_id`, `log_action`, `is_valid_color`, `process_task_data`, constantes de helpers, `Task.validate_status/validate_priority/is_overdue`, `User.is_admin` e toda a `NotificationService`. Dependências `marshmallow`, `requests` e `python-dotenv` estão no manifesto sem nenhum import.
Impact: Ruído na leitura, falsa sensação de que validações existem e dependências instaladas sem necessidade.
Recommendation: Remover imports e código mortos; reaproveitar o que tem valor (`is_overdue`, `calculate_percentage`, constantes) na nova estrutura e limpar o manifesto (Playbook T12).

### #20 [LOW] `print` no lugar de logger (AP21)
File: routes/task_routes.py:149, 153, 219, 234
routes/user_routes.py:83, 89, 147
services/notification_service.py:21, 24
utils/helpers.py:39, 41
Description: Eventos e erros registrados com `print(f"Task criada: {task.id} - {task.title}")`, `print(f"ERRO: {str(e)}")` etc. (Os `print` de `seed.py:93-96` são saída de script CLI e não entram no finding.)
Impact: Sem nível, sem timestamp padronizado e sem como desligar/redirecionar em produção.
Recommendation: Usar `logging.getLogger(__name__)` configurado no boot (Playbook T14).

### #21 [LOW] Condicionais verbosas (AP22)
File: models/task.py:40-43, 46-48, 51-60
models/user.py:35-38
utils/helpers.py:21-23, 53-55, 103
routes/task_routes.py:141, 210
Description: `if new_status in valid: return True else: return False`, `if self.role == 'admin': return True else: return False`, três `if` aninhados em `is_overdue`, e `type(tags) == list` em vez de `isinstance`.
Impact: Código mais longo e propenso a erro sem ganho de clareza.
Recommendation: Retornar a expressão booleana direto e usar `isinstance(tags, list)` (Playbook T12).

## Deprecated APIs
- #14 `Model.query.get(id)` → `db.session.get(Model, id)` (routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227; routes/user_routes.py:29, 94, 136, 155; routes/report_routes.py:105, 192, 213)
- #15 `datetime.utcnow()` → `datetime.now(timezone.utc)` (models/task.py:15, 16, 52; models/user.py:14; models/category.py:11; routes/task_routes.py:31, 72, 215, 285; routes/user_routes.py:172; routes/report_routes.py:35, 42, 45, 71, 133; services/notification_service.py:35; utils/helpers.py:38; seed.py:66-74)

## Architecture Notes
Arquitetura em camadas parciais: `models/` com SQLAlchemy já está correto e será preservado (ajustando senha, serialização e datas), mas as rotas são fat controllers que falam direto com o ORM e repetem regras, não há config isolada, controllers, error handler central nem autenticação. Não há SQL Injection: todo acesso é via ORM e o `.like(f'%{query}%')` de `search_tasks` é parametrizado.
Direção: criar `config/` (env vars), `controllers/` (request/response), `services/` (regras de task, user, category, report, auth), `middlewares/` (auth + error handlers), manter `routes/` como blueprints finos (com categorias em arquivo próprio) e `app.py` como factory preservando `python app.py`. `utils/helpers.py` e `NotificationService` mortos serão removidos ou absorvidos.

================================
Total: 21 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
