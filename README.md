# Desafio — Skill `refactor-arch`: Auditoria e Refatoração Arquitetural

Skill para Claude Code que analisa um projeto backend legado, audita o código contra um catálogo de anti-patterns e refatora para o padrão MVC, validando que a aplicação continua funcionando. Foi executada em 3 projetos: dois em Python/Flask e um em Node.js/Express.

```
mba-ia-refactor-projects-skill/
├── README.md
├── code-smells-project/      # Projeto 1 — Python/Flask (E-commerce)   + .claude/skills/refactor-arch/
├── ecommerce-api-legacy/     # Projeto 2 — Node.js/Express (LMS)      + .claude/skills/refactor-arch/
├── task-manager-api/         # Projeto 3 — Python/Flask (Tasks)       + .claude/skills/refactor-arch/
└── reports/
    ├── audit-project-1.md
    ├── audit-project-2.md
    └── audit-project-3.md
```

---

## A) Análise Manual

Antes de escrever a skill, li o código dos três projetos para entender quais padrões ela teria que detectar. As linhas abaixo se referem ao código **original**, antes da refatoração.

### Projeto 1 — code-smells-project (Python/Flask, API de E-commerce)

4 arquivos (`app.py`, `controllers.py`, `models.py`, `database.py`), cerca de 780 linhas. Não há separação de camadas: `models.py` mistura SQL, regra de negócio e formatação de 3 domínios, e `app.py` tem rotas administrativas com acesso direto ao banco.

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | SQL Injection: todas as queries são montadas por concatenação de strings | `models.py:28, 47-50, 57-61, 68, 92, 110, 127-128, 140, 148-150, 280, 291-297` | Em `login_usuario` (linha 110), um e-mail `' OR '1'='1' --` autentica sem senha. Na busca (linha 291), dá para ler qualquer tabela. |
| 2 | CRITICAL | Endpoint que executa SQL arbitrário e endpoint que apaga o banco, sem autenticação | `app.py:47-57` (`/admin/reset-db`), `app.py:59-78` (`/admin/query`) | Qualquer pessoa na rede pode rodar `DROP TABLE` ou apagar todos os dados com um POST. |
| 3 | CRITICAL | Credenciais hardcoded e expostas em endpoint público | `app.py:7` (`SECRET_KEY`), `controllers.py:285-289` (`/health` devolve `secret_key`, `db_path` e `debug`) | O segredo usado para assinar sessões está no repositório e ainda é devolvido para qualquer cliente que chame `/health`. |
| 4 | CRITICAL | Senhas em texto puro, comparadas no SQL e devolvidas na listagem de usuários | `database.py:76-78`, `models.py:83, 99, 110, 127-128` | `GET /usuarios` devolve a senha de todos os usuários, inclusive a do admin. |
| 5 | HIGH | Estado global mutável: uma única conexão SQLite global compartilhada entre threads | `database.py:4-10` (`global db_connection`, `check_same_thread=False`) | O servidor do Flask é multi-thread. Requisições concorrentes compartilham o mesmo cursor/transação, e um erro numa requisição deixa escrita pendente que vai ser commitada pela próxima. |
| 6 | HIGH | Debug ligado e servidor exposto em `0.0.0.0` | `app.py:8, 88` | O debugger do Werkzeug permite executar código Python pelo navegador se alguém conseguir o PIN. |
| 7 | HIGH | Regra de negócio e efeitos colaterais espalhados entre model e controller | `models.py:133-169` (pedido calcula total, valida estoque e baixa estoque sem transação), `controllers.py:208-210, 247-250` (notificações "fake" com `print`) | Não dá para testar a criação de pedido sem banco nem HTTP, e uma falha no meio do loop deixa o pedido sem itens. |
| 8 | MEDIUM | Queries N+1 na listagem de pedidos | `models.py:187-199`, `models.py:219-231` | Para cada pedido, uma query de itens e, para cada item, outra query de produto. 100 pedidos com 3 itens viram cerca de 400 queries. |
| 9 | MEDIUM | Código duplicado | Serialização de produto em `models.py:12-21, 31-40, 304-313`; `get_pedidos_usuario` e `get_todos_pedidos` quase idênticos (`models.py:171-233`); validação de produto copiada (`controllers.py:28-50` e `72-90`) | Toda alteração de campo precisa ser feita em 3 lugares, e as validações de criar e atualizar já divergem (o atualizar não valida categoria nem tamanho do nome). |
| 10 | MEDIUM | Error handling repetido e vazando detalhes internos | `try/except Exception as e: return {"erro": str(e)}, 500` em todas as funções de `controllers.py` | Mensagens de exceção do SQLite chegam ao cliente e não existe um ponto central para tratar erro. |
| 11 | LOW | Magic numbers / listas literais | `models.py:257-262` (faixas de desconto 10000/5000/1000 e taxas 0.1/0.05/0.02), `controllers.py:52` (categorias), `controllers.py:242` (status) | Regra de negócio escondida em números soltos, difícil de achar e de alterar. |
| 12 | LOW | `print` usado como log, inclusive com e-mail do usuário | `controllers.py:8, 57, 106, 161, 179, 182, 208-210, 219` | Não tem nível, nem destino configurável, e expõe dado pessoal no stdout. |
| 13 | LOW | Imports sem uso e nomes que sombreiam builtins | `models.py:2` (`import sqlite3`), `database.py:2` (`import os`), `app.py:1` (`request` usado só no admin), parâmetro `id` em várias funções | É ruído, e `id` sombreia a função builtin do Python. |

### Projeto 2 — ecommerce-api-legacy (Node.js/Express, LMS com checkout)

3 arquivos em `src/`, cerca de 180 linhas. A classe `AppManager` é uma God Class: cria o banco em memória, define o schema, faz o seed, registra as rotas e contém toda a regra de checkout e relatório.

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Credenciais hardcoded (senha do banco e chave **live** do gateway de pagamento) | `src/utils.js:1-7` | Uma chave `pk_live_` commitada no repositório é exatamente o tipo de vazamento que gera fraude. |
| 2 | CRITICAL | God Class `AppManager` (banco + schema + seed + rotas + regra) | `src/AppManager.js:4-139` | Nada pode ser testado isoladamente. O checkout sozinho tem 50 linhas e 5 níveis de callback. |
| 3 | CRITICAL | Número do cartão e chave do gateway impressos no log | `src/AppManager.js:45` | Viola PCI-DSS: o número completo do cartão vai parar no stdout/arquivo de log. |
| 4 | CRITICAL | "Hash" de senha caseiro e reversível; senha padrão quando não informada | `src/utils.js:17-23` (`badCrypto` = base64 truncado), `src/AppManager.js:68` (`p \|\| "123456"`), seed com senha `'123'` em texto puro (linha 18) | Base64 não é hash: os 10 caracteres guardados são os 2 primeiros do base64 repetidos, então senhas com o mesmo começo colidem e dá para recuperar o início da senha. |
| 5 | HIGH | Endpoints administrativos e destrutivos sem autenticação | `src/AppManager.js:80` (`/api/admin/financial-report`), `src/AppManager.js:131` (`DELETE /api/users/:id`) | Qualquer cliente vê o faturamento e o nome de todos os alunos, ou apaga usuários. |
| 6 | HIGH | Checkout multi-etapa sem transação, em callback hell, com erros ignorados | `src/AppManager.js:37-77` (matrícula → pagamento → auditoria), `57` (`err` ignorado), `92` (`enrollments` sem checar `err`) | Se o INSERT do pagamento falhar, a matrícula já foi criada: o aluno fica matriculado sem pagar. |
| 7 | HIGH | Estado global mutável | `src/utils.js:9-15` (`globalCache`, `totalRevenue`) | Um cache em objeto global cresce sem limite e é compartilhado entre requisições. `totalRevenue` é exportado como primitivo, então nunca reflete nada. |
| 8 | MEDIUM | Queries N+1 no relatório financeiro, controladas por contadores manuais | `src/AppManager.js:89-127` | Uma query por curso, uma por matrícula e outra por pagamento, com `coursesPending`/`enrPending` decidindo quando responder. É frágil e lento. |
| 9 | MEDIUM | Integridade referencial ignorada ao deletar usuário | `src/AppManager.js:131-137` | Matrículas e pagamentos ficam órfãos (a própria resposta admite: "ficaram sujos no banco"), e o erro do DELETE é ignorado. |
| 10 | MEDIUM | Validação fraca e regra de pagamento simulada inline | `src/AppManager.js:35` (só checa presença), `46` (`cc.startsWith("4")` decide aprovação) | Cartão, e-mail e `c_id` não são validados. A decisão de pagamento fica presa dentro da rota. |
| 11 | MEDIUM | Respostas e erros sem padrão | `res.send("Bad Request")`, `res.status(500).send("Erro DB")` em texto e sucesso em JSON; sem middleware de erro | O cliente precisa tratar dois formatos e uma exceção não tratada derruba o processo. |
| 12 | LOW | Nomes ruins | `src/AppManager.js:29-33` (`u`, `e`, `p`, `cid`, `cc`), `badCrypto`, `AppManager`, campos `usr`/`eml`/`pwd` | O código fica difícil de ler, e `e` costuma significar "erro", não "e-mail". |
| 13 | LOW | Código morto | `totalRevenue` importado e nunca usado (`AppManager.js:2`), `dbUser`/`dbPass`/`smtpUser` nunca lidos (`utils.js:2-5`) | É ruído e passa a falsa impressão de que existe integração com banco/SMTP. |
| 14 | LOW | `console.log` como log | `src/AppManager.js:45`, `src/utils.js:13`, `src/app.js:13` | Não tem nível nem destino configurável. |

### Projeto 3 — task-manager-api (Python/Flask, Task Manager)

Já tem `models/`, `routes/`, `services/` e `utils/`, mas as rotas acessam o ORM direto, carregam toda a regra de negócio, e não existe camada de controller, config nem error handler. É o projeto mais "enganoso": parece organizado, mas tem problemas de segurança tão graves quanto os outros.

| # | Severidade | Problema | Local | Por que é relevante |
|---|---|---|---|---|
| 1 | CRITICAL | Senha com MD5 sem salt | `models/user.py:27-32` | MD5 é quebrado por rainbow table em segundos. As senhas do seed (`1234`, `abcd`) seriam recuperadas na hora. |
| 2 | CRITICAL | Hash de senha devolvido nas respostas da API | `models/user.py:21` (`to_dict` inclui `password`), usado em `routes/user_routes.py:33, 85, 129, 209` | Somado ao MD5, qualquer `GET /users/1` ou login entrega a senha praticamente em claro. |
| 3 | CRITICAL | Credenciais hardcoded | `app.py:13` (`SECRET_KEY`), `services/notification_service.py:9-10` (usuário e senha do SMTP) | Segredos versionados e iguais em todos os ambientes. |
| 4 | HIGH | Autenticação falsa e nenhuma rota protegida | `routes/user_routes.py:210` (`'fake-jwt-token-' + str(user.id)`) | O "token" é previsível e nunca é verificado. Qualquer um apaga usuários e altera roles. |
| 5 | HIGH | Regra de negócio dentro das rotas (sem controllers/services) | `routes/report_routes.py:12-101` (relatório inteiro calculado na rota), `routes/task_routes.py:11-63` | As rotas fazem query, cálculo e serialização. O `NotificationService` existe, mas ninguém usa. |
| 6 | HIGH | Debug ligado e bind em `0.0.0.0` | `app.py:34` | Mesmo risco do projeto 1: debugger interativo exposto. |
| 7 | MEDIUM | Queries N+1 | `routes/task_routes.py:41-57` (`User.query.get` e `Category.query.get` por task), `routes/user_routes.py:22` (`len(u.tasks)`), `routes/report_routes.py:55-57, 161-163` | Uma listagem de N tasks gera 2N+1 queries, mesmo com relationships já declarados no model. |
| 8 | MEDIUM | Lógica de "task atrasada" duplicada 6 vezes, mesmo existindo `Task.is_overdue()` | `routes/task_routes.py:30-39, 71-80, 283-287`, `routes/report_routes.py:33-36, 132-135`, `routes/user_routes.py:171-180` vs `models/task.py:50-60` | Se a regra mudar, alguém vai esquecer um dos 6 lugares. |
| 9 | MEDIUM | APIs deprecated | `Model.query.get()` (API legada do SQLAlchemy 2.x) em `routes/task_routes.py:42, 51, 67, 117, 122, 158, 188, 195, 227` e nos outros arquivos de rotas; `datetime.utcnow()` (deprecated no Python 3.12) nos models e rotas | Gera warning hoje e vai quebrar em versões futuras. O equivalente moderno é `db.session.get(Model, id)` e `datetime.now(timezone.utc)`. |
| 10 | MEDIUM | `except:` sem tipo e validação de tipo ausente | `routes/task_routes.py:62, 137, 204, 236`, `routes/report_routes.py:186, 207, 221`, `routes/user_routes.py:130, 149`; `routes/task_routes.py:113` compara `priority` sem converter | `"priority": "alta"` gera `TypeError` e um 500 genérico. O bare except esconde até `KeyboardInterrupt`. |
| 11 | MEDIUM | Responsabilidade no lugar errado: CRUD de categorias dentro de `report_routes.py` | `routes/report_routes.py:157-223` | Quem procura a rota de categorias não acha. É sinal de que a divisão em camadas é só cosmética. |
| 12 | LOW | Imports sem uso | `app.py:7` (`os, sys, json`), `routes/task_routes.py:7` (`json, os, sys, time`), `routes/user_routes.py:6` (`hashlib, json`), `routes/report_routes.py:7-8`, `utils/helpers.py:3-7` | É ruído e esconde as dependências reais de cada módulo. |
| 13 | LOW | Magic numbers/strings e constantes que existem mas não são usadas | Listas de status e roles literais nas rotas; `utils/helpers.py:110-116` define `VALID_STATUSES`, `MAX_TITLE_LENGTH` etc. e ninguém importa | A intenção já estava lá, mas nunca foi aplicada. |
| 14 | LOW | Condicionais verbosas | `models/task.py:38-60`, `models/user.py:34-38` | `if x: return True else: return False` em vez de `return x`. |

---

## B) Construção da Skill

### Estrutura

```
.claude/skills/refactor-arch/
├── SKILL.md                              # o "prompt": fases, ordem, formato de saída, regras de parada
└── references/
    ├── project-analysis.md               # Fase 1 — heurísticas de linguagem, framework, banco, domínio, arquitetura
    ├── anti-patterns-catalog.md          # Fase 2 — 22 anti-patterns com sinais de detecção e severidade
    ├── report-template.md                # Fase 2 — formato obrigatório do relatório
    ├── mvc-guidelines.md                 # Fase 3 — camadas, regras de dependência, estrutura alvo
    └── refactoring-playbook.md           # Fase 3 — 14 transformações com código antes/depois
```

### Decisões de design

- **SKILL.md enxuto, conhecimento nas referências.** O SKILL.md diz *o que fazer e em que ordem*; as referências dizem *como*. Cada fase manda ler só os arquivos que ela precisa, para não encher o contexto com o playbook antes da hora.
- **Formatos de saída fixos.** Os blocos `PHASE 1`, o relatório e o `PHASE 3` têm template literal, o que permite comparar a execução nos 3 projetos e conferir o checklist.
- **Pausa obrigatória.** A Fase 2 termina com `Proceed with refactoring (Phase 3)? [y/n]` e a instrução explícita de PARAR. O único arquivo que pode ser criado antes da confirmação é o relatório.
- **`disable-model-invocation: true`.** Por ser uma skill que reescreve o projeto inteiro, ela só roda quando chamada explicitamente com `/refactor-arch`, nunca porque o modelo achou que era uma boa ideia.
- **Baseline antes de refatorar.** A Fase 3 primeiro sobe a aplicação original e grava status code e formato de cada endpoint, e só então refatora e compara. Sem isso, "os endpoints continuam respondendo" seria só uma afirmação.
- **Contrato público preservado.** Paths, métodos, status e chaves de resposta não mudam. Quando a correção de segurança exige mudar algo (ex.: não devolver senha), a skill lista em "Intentional Behavior Changes".
- **IDs cruzados.** Cada anti-pattern (AP01–AP22) aponta para a transformação do playbook (T1–T14) que o resolve, e o relatório cita os dois. Isso deixa a Fase 3 rastreável.

### Anti-patterns do catálogo

| Severidade | Anti-patterns | Motivo da inclusão |
|---|---|---|
| CRITICAL | AP01 Credenciais hardcoded, AP02 SQL Injection, AP03 God Class, AP04 Endpoint sensível sem auth, AP05 Senha insegura, AP06 Exposição de dados sensíveis | Apareceram nos 3 projetos de alguma forma e são os que geram incidente real |
| HIGH | AP07 Fat Controller, AP08 Acoplamento sem DI, AP09 Estado global, AP10 Multi-etapa sem transação / callback hell, AP11 Debug/CORS inseguro | Violações de SOLID/MVC que impedem testar e evoluir |
| MEDIUM | AP12 N+1, AP13 Validação, AP14 Error handling, AP15 Duplicação, AP16 **APIs deprecated**, AP17 Integridade referencial | Performance e padronização; AP16 tem uma tabela por stack (SQLAlchemy, Python 3.12, Flask, Node, Express) |
| LOW | AP18 Magic numbers, AP19 Nomes ruins, AP20 Código morto, AP21 print/console.log, AP22 Condicionais verbosas | Legibilidade |

Cada item tem **sinais de detecção concretos** (ex.: "query dentro de `for` sobre resultado de outra query", "`grep` por `secret|pass|key` atribuído a literal") e também o que **não** é finding (ex.: `.like(f'%{q}%')` do SQLAlchemy é parametrizado), para reduzir falso positivo.

### Agnosticismo de tecnologia

- As heurísticas da Fase 1 são tabelas de sinais por linguagem/framework (Python, Node, TS, Go, Java, PHP, Ruby, C#), e não regras específicas destes 3 projetos.
- O catálogo descreve o problema de forma conceitual e dá sinais de detecção nas duas sintaxes.
- O playbook mostra cada transformação em Python **e** JavaScript sempre que a sintaxe muda bastante.
- `mvc-guidelines.md` tem uma regra de **adaptação ao nível de organização**: monolito → estrutura completa em `src/`; projeto já em camadas → preservar o que está certo e criar só o que falta (controllers, config, middlewares).
- A validação descobre como subir a aplicação (README → `package.json` → `__main__`/`listen`), em vez de assumir um comando.

### Desafios encontrados

<!-- REVISAR: escreva com suas palavras o que achou mais difícil. Os pontos abaixo são o que de fato aconteceu durante as execuções. -->

- **Projeto parcialmente organizado.** O risco no task-manager era a skill olhar as pastas `models/routes/services` e concluir que já estava em MVC. Resolvi com a classificação "Camadas parciais" na análise (as pastas existem, mas as rotas acessam o ORM e têm regra) e com a regra de adaptação nas guidelines. Na execução, a skill manteve `models/` e `routes/` no lugar, criou `controllers/`, `config/` e `middlewares/`, e ainda tirou o CRUD de categorias de dentro de `report_routes.py`.
- **Provar que "continua funcionando".** Sem baseline, o agente poderia declarar sucesso sem testar. Daí o passo obrigatório de baseline e a comparação endpoint a endpoint. A baseline acabou pegando coisas que a leitura do código não pegou:
  - no projeto 2, um `card` numérico derrubava o processo Node inteiro (`TypeError: cc.startsWith is not a function`);
  - no projeto 3, ela mostrou que o finding #16 estava parcialmente errado (o ORM já anulava `category_id` ao apagar categoria), e o relatório foi corrigido;
  - também no projeto 3, a comparação de valores mostrou que o seed novo inseria as tasks em outra ordem e mudava os ids, e isso foi corrigido.
- **Correções de segurança x contrato.** Hash de senha, proteção das rotas administrativas e remoção da senha das respostas mudam o comportamento de propósito. Criei a seção "Intentional Behavior Changes" para separar quebra acidental de mudança proposital, e a validação testa essas rotas com e sem credencial.
- **Portas fixas no código original.** Os dois projetos Flask usam a 5000 fixa. Para a baseline, a skill orienta subir com outra porta pelo CLI do framework; depois da refatoração, a porta vem da config.
- **Iteração na skill.** Na primeira rodada, a árvore planejada do projeto 3 não foi impressa antes da edição, e no projeto 1 a remoção dos arquivos legados foi bloqueada pela permissão do Claude Code. Ajustei o SKILL.md para exigir o `## Planned Structure` antes do primeiro arquivo editado e para, em caso de bloqueio, listar os arquivos e pedir ao usuário em vez de tentar contornar.

---

## C) Resultados

### Resumo das auditorias

| Projeto | Stack | Arquivos | CRITICAL | HIGH | MEDIUM | LOW | Total | Relatório |
|---|---|---|---|---|---|---|---|---|
| 1 — code-smells-project | Python + Flask 3.1.1 | 4 (~780 linhas) | 6 | 5 | 5 | 5 | **21** | [audit-project-1.md](reports/audit-project-1.md) |
| 2 — ecommerce-api-legacy | Node.js + Express 4.18 | 3 (~180 linhas) | 5 | 4 | 7 | 4 | **20** | [audit-project-2.md](reports/audit-project-2.md) |
| 3 — task-manager-api | Python + Flask 3.0.0 | 15 (~1160 linhas) | 4 | 4 | 8 | 5 | **21** | [audit-project-3.md](reports/audit-project-3.md) |

Comparando com a análise manual, a skill encontrou todos os problemas que eu tinha listado nos 3 projetos e mais alguns que eu não tinha visto. Exemplos: no projeto 1, `quantidade` negativa no pedido **aumenta** o estoque e `PUT /pedidos/<id>/status` devolve 200 para pedido inexistente; no projeto 3, qualquer anônimo podia criar usuário com `role: admin`.

APIs deprecated detectadas:
- Projeto 3: `Model.query.get()` (16 ocorrências) e `datetime.utcnow()`.
- Projeto 2: a API só de callback do `sqlite3`. A skill também listou o que verificou e **não** encontrou (`new Buffer`, `body-parser`, `res.send(status)`...).
- Projeto 1: a skill relatou explicitamente que não encontrou nenhuma.

### Antes x Depois

**Projeto 1 — code-smells-project** (monolito → MVC completo em `src/`)

```
ANTES                         DEPOIS
app.py         (misto)        app.py                      # shim: mantém `python app.py`
controllers.py (misto)        .env.example
models.py      (God File)     src/
database.py    (global)       ├── app.py                  # create_app(): composition root
requirements.txt              ├── database.py             # conexão por request (flask.g), schema com FK, transacao()
                              ├── config/                 # settings.py (env), constants.py
                              ├── models/                 # produto, usuario, pedido, sistema
                              ├── services/               # pedido, relatorio, notificacao
                              ├── controllers/            # produto, usuario, pedido, relatorio, sistema
                              ├── views/                  # blueprints por domínio
                              ├── middlewares/            # error_handler.py, auth.py (X-Admin-Token)
                              └── utils/                  # errors.py, validators.py
```

**Projeto 2 — ecommerce-api-legacy** (God Class → MVC com injeção de dependência)

```
ANTES                         DEPOIS
src/                          .env.example
├── app.js                    src/
├── AppManager.js (God Class) ├── app.js                  # createApp({ db, settings }) + listen
└── utils.js  (config+estado) ├── config/                 # settings.js (env), constants.js
                              ├── database/connection.js  # wrapper Promise, transaction(), schema com FK + CASCADE
                              ├── models/                 # user, course, enrollment, payment, auditLog
                              ├── services/               # checkoutService (transação), reportService (1 query JOIN)
                              ├── controllers/            # checkout, report, user
                              ├── views/routes.js         # express.Router + asyncHandler
                              ├── middlewares/            # errorHandler.js, auth.js (adminOnly)
                              └── utils/                  # errors, validators, logger, password (scrypt)
```

**Projeto 3 — task-manager-api** (camadas parciais → camadas completas, sem mover o que já estava certo)

```
ANTES                         DEPOIS
app.py                        app.py                      # create_app(settings)
database.py                   database.py
seed.py                       seed.py                     # usa create_app()
models/   (MD5, to_dict c/ senha)  models/                # werkzeug hash, sem password no to_dict, utcnow() helper
routes/   (fat controllers)   routes/                     # blueprints finos: task, user, category, report, auth, health
services/ (morto)             services/                   # task, user, category, report, auth
utils/    (quase tudo morto)  controllers/                # novo
                              config/                     # novo: settings.py, constants.py
                              middlewares/                # novo: auth.py (token assinado), error_handler.py
                              utils/                      # errors.py, validators.py, helpers.py
```

### Checklist de validação

| Item | P1 | P2 | P3 |
|---|---|---|---|
| **Fase 1** — Linguagem detectada corretamente | ✅ Python | ✅ JavaScript/Node | ✅ Python |
| Framework detectado corretamente | ✅ Flask 3.1.1 | ✅ Express 4.18 | ✅ Flask 3.0.0 + SQLAlchemy |
| Domínio descrito corretamente | ✅ E-commerce | ✅ LMS com checkout | ✅ Task Manager |
| Nº de arquivos condiz com a realidade | ✅ 4 | ✅ 3 | ✅ 15 |
| **Fase 2** — Relatório segue o template | ✅ | ✅ | ✅ |
| Cada finding com arquivo e linhas exatos | ✅ | ✅ | ✅ |
| Ordenado CRITICAL → LOW | ✅ | ✅ | ✅ |
| Mínimo de 5 findings | ✅ 21 | ✅ 20 | ✅ 21 |
| APIs deprecated incluídas | ✅ (nenhuma, declarado) | ✅ | ✅ |
| Pausa e pede confirmação antes da Fase 3 | ✅ | ✅ | ✅ |
| **Fase 3** — Estrutura segue MVC | ✅ | ✅ | ✅ |
| Config extraída (sem hardcoded) | ✅ | ✅ | ✅ |
| Models abstraem dados | ✅ | ✅ | ✅ |
| Views/Routes separadas | ✅ | ✅ | ✅ |
| Controllers concentram o fluxo | ✅ | ✅ | ✅ |
| Error handling centralizado | ✅ | ✅ | ✅ |
| Entry point claro | ✅ `python app.py` | ✅ `npm start` | ✅ `python app.py` |
| Aplicação inicia sem erros | ✅ | ✅ | ✅ |
| Endpoints originais respondem | ✅ 19/19 | ✅ 3/3 | ✅ 22/22 |

### Logs das aplicações rodando após a refatoração

**Projeto 1** — `PORT=5201 ADMIN_TOKEN=dev-token python app.py`
```
WARNING src.app: SECRET_KEY não definida; usando chave aleatória (apenas para desenvolvimento)
INFO src.app: Servidor iniciado em http://127.0.0.1:5201
 * Serving Flask app 'src.app'
 * Debug mode: off
"GET / HTTP/1.1" 200
"GET /health HTTP/1.1" 200
"GET /produtos HTTP/1.1" 200
"GET /produtos/busca?q=Mouse HTTP/1.1" 200
"GET /produtos/1 HTTP/1.1" 200
INFO src.controllers.produto_controller: Produto criado com id=11
"POST /produtos HTTP/1.1" 201
"GET /usuarios HTTP/1.1" 200                      # sem o campo senha
INFO src.services.notificacao_service: Notificação (email/sms/push): pedido 1 criado para usuario_id=2
"POST /pedidos HTTP/1.1" 201
"GET /pedidos HTTP/1.1" 200
"GET /relatorios/vendas HTTP/1.1" 200
INFO src.controllers.usuario_controller: Falha de login
"POST /login HTTP/1.1" 401                        # email = "' OR '1'='1' --" (SQL injection bloqueado)
"POST /admin/query HTTP/1.1" 403                  # sem X-Admin-Token
```

**Projeto 2** — `PORT=3202 ADMIN_TOKEN=dev-token npm start`
```
[2026-10-06T02:55:31.612Z] INFO Frankenstein LMS rodando na porta 3202...
[2026-10-06T02:55:31.767Z] INFO Checkout aprovado: matrícula 2, cartão final 4444

$ POST /api/checkout (sucesso)
{"msg":"Sucesso","enrollment_id":2}  -> HTTP 200
$ POST /api/checkout (recusado)
Pagamento recusado  -> HTTP 400
$ GET /api/admin/financial-report (com X-Admin-Token)
[{"course":"Clean Architecture","revenue":997,"students":[{"student":"Leonan","paid":997}]},{"course":"Docker","revenue":497,"students":[{"student":"Guilherme","paid":497}]}]  -> HTTP 200
$ GET /api/admin/financial-report (sem token)
Acesso negado  -> HTTP 403
$ DELETE /api/users/1 (com X-Admin-Token)
Usuário deletado  -> HTTP 200
```
Antes, o mesmo checkout imprimia `Processando cartão 4111222233334444 na chave pk_live_1234567890abcdef`. Agora só aparecem os 4 últimos dígitos.

**Projeto 3** — `PORT=5203 SECRET_KEY=dev-secret python seed.py && python app.py`
```
Seed concluído com sucesso!
  3 usuários
  4 categorias
  10 tasks
 * Serving Flask app 'app'
 * Debug mode: off
 * Running on http://127.0.0.1:5203

GET /                      -> 200
GET /health                -> 200
GET /tasks                 -> 200
GET /tasks/1               -> 200
GET /tasks/search?q=login  -> 200
GET /tasks/stats           -> 200
GET /users                 -> 200
GET /users/1               -> 200
GET /users/1/tasks         -> 200
GET /reports/summary       -> 200
GET /reports/user/1        -> 200
GET /categories            -> 200
POST /tasks               -> 201
POST /tasks priority="x"  -> 400      # antes: 500 com TypeError
POST /login (password fora da resposta) -> ok
DELETE /tasks/11 sem token  -> 401
DELETE /tasks/11 com token  -> 200
INFO services.auth_service: Login realizado: usuario_id=1
```
Nos 3 casos, a validação da própria skill comparou endpoint a endpoint com a baseline do código original. O detalhe de cada um está no resumo da Fase 3 de cada execução, e as mudanças intencionais de comportamento estão listadas abaixo.

### Mudanças intencionais de comportamento

- **P1:** `GET /usuarios` não devolve mais `senha`. `/health` não devolve mais `secret_key`/`db_path`. `/admin/*` exige o header `X-Admin-Token`, e `/admin/query` agora é somente leitura. Erros de entrada que antes davam 500 agora dão 400. `DELETE /produtos/<id>` com pedidos retorna 409.
- **P2:** `/api/admin/financial-report` e `DELETE /api/users/:id` exigem `X-Admin-Token`. O delete apaga em cascata matrículas e pagamentos. Um checkout recusado não grava mais o usuário. Payload inválido dá 400 em vez de derrubar o servidor.
- **P3:** `password` saiu de todas as respostas. O `token` do login agora é assinado e expira. `DELETE /tasks|categories` exige token. Excluir usuário e alterar `role`/`active` exige token de admin.

### Comportamento da skill em stacks diferentes

- **Mesma skill, decisões diferentes.** No projeto 1 (monolito), a skill criou a estrutura completa em `src/` e manteve um `app.py` na raiz para não quebrar o `python app.py`. No projeto 3, já em camadas, ela preservou `models/` e `routes/` e só criou as camadas que faltavam. No projeto 2, ela trocou a God Class por factories com injeção de dependência, que é o idioma natural de Express.
- **Severidade contextual.** No projeto 3, `report_routes.py` foi classificado como God File HIGH, e não CRITICAL, com a justificativa de que ele não abre conexão nem guarda config. No projeto 2, a configuração insegura (AP11) caiu para MEDIUM porque não havia debug nem CORS aberto. A regra do catálogo de subir ou descer a severidade com justificativa funcionou.
- **Falsos positivos evitados.** Os projetos 2 e 3 não têm SQL Injection: o 2 usa placeholders e o 3 usa ORM. A skill não inventou o finding e registrou isso nas Architecture Notes.
- **O que ficou para depois.** No P1, `/login` continua sem emitir token, porque isso mudaria o contrato. No P3, `PUT /users/<id>` ainda permite alterar nome/e-mail/senha sem autenticação; só `role`/`active` foram protegidos. Os dois pontos foram registrados pela própria skill como pendências.

<!-- REVISAR: adicione aqui suas impressões pessoais (o que achou do resultado, o que faria diferente). Se quiser screenshots, rode os comandos da seção D e tire print do terminal. -->

---

## D) Como Executar

### Pré-requisitos

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) instalado e autenticado (`claude --version`)
- Python 3.10+ (projetos 1 e 3)
- Node.js 18+ e npm (projeto 2)

### Executar a skill

A skill fica dentro de cada projeto em `.claude/skills/refactor-arch/`. Rode o Claude Code a partir da pasta do projeto:

```bash
# Projeto 1
cd code-smells-project
claude "/refactor-arch"

# Projeto 2
cd ../ecommerce-api-legacy
claude "/refactor-arch"

# Projeto 3
cd ../task-manager-api
claude "/refactor-arch"
```

A skill imprime a Fase 1, gera o relatório da Fase 2 (também salvo em `reports/audit-report.md` dentro do projeto) e pergunta `Proceed with refactoring (Phase 3)? [y/n]`. Responda `y` para refatorar.

### Validar a refatoração

**Projeto 1**
```bash
cd code-smells-project
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python app.py
curl http://localhost:5000/health
curl http://localhost:5000/produtos
```

**Projeto 2**
```bash
cd ecommerce-api-legacy
npm install
ADMIN_TOKEN=dev-token npm start
curl -X POST http://localhost:3000/api/checkout -H "Content-Type: application/json" \
  -d '{"usr":"Guilherme","eml":"gui@fullcycle.com.br","pwd":"senhaforte","c_id":2,"card":"4111222233334444"}'
curl -H "X-Admin-Token: dev-token" http://localhost:3000/api/admin/financial-report
```
O `api.http` do projeto já tem os exemplos com o header de admin.

**Projeto 3**
```bash
cd task-manager-api
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python seed.py
python app.py
curl http://localhost:5000/tasks
curl http://localhost:5000/reports/summary
# rotas destrutivas exigem o token devolvido pelo /login
TOKEN=$(curl -s -X POST http://localhost:5000/login -H "Content-Type: application/json" \
  -d '{"email":"joao@email.com","password":"1234"}' | python -c 'import sys,json; print(json.load(sys.stdin)["token"])')
curl -X DELETE -H "Authorization: Bearer $TOKEN" http://localhost:5000/tasks/1
```

As variáveis de ambiente aceitas por cada projeto estão no respectivo `.env.example`.
