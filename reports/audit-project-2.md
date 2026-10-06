================================
ARCHITECTURE AUDIT REPORT
================================
Project: ecommerce-api-legacy
Stack:   JavaScript (Node.js, CommonJS) + Express 4.18 (^4.18.2, lock 4.22.1)
Files:   3 analyzed | ~180 lines of code
Date:    2026-10-05

## Summary
CRITICAL: 5 | HIGH: 4 | MEDIUM: 7 | LOW: 4

## Findings

### #1 [CRITICAL] Credenciais / segredos hardcoded (AP01)
File: src/utils.js:1-7
Description: Objeto `config` literal com segredos de produção no código: `dbUser: "admin_master"` (linha 2), `dbPass: "senha_super_secreta_prod_123"` (linha 3), `paymentGatewayKey: "pk_live_1234567890abcdef"` (linha 4) e `smtpUser: "no-reply@fullcycle.com.br"` (linha 5). Nenhuma leitura de `process.env`.
Impact: Qualquer pessoa com acesso ao repositório obtém a senha do banco e a chave live do gateway de pagamento; impossível ter valores diferentes por ambiente ou rotacionar a chave sem novo deploy.
Recommendation: Mover configuração para `src/config/` lendo `process.env` com fallback seguro só para desenvolvimento, documentar em `.env.example` e remover os segredos do código (Playbook T1).

### #2 [CRITICAL] God Class / God File (AP03)
File: src/AppManager.js:4-139
src/utils.js:1-25
Description: A classe `AppManager` abre a conexão (`new sqlite3.Database(':memory:')`, linha 7), cria schema e seed (`initDb`, linhas 10-23), registra todas as rotas (`setupRoutes`, linhas 25-138), contém as regras de pagamento/matrícula/relatório e formata as respostas. O handler de checkout tem 51 linhas (28-78) e callbacks aninhados em 6 níveis. `utils.js` mistura config, cache em memória e "criptografia" (`badCrypto`).
Impact: Impossível testar regras de negócio sem subir Express e SQLite; qualquer mudança em um fluxo (checkout, relatório, usuários) mexe no mesmo arquivo e arrisca quebrar os outros.
Recommendation: Separar em `config/`, `database/` (conexão + schema/seed), `models/` (acesso a dados por entidade), `services/` (regras), `controllers/` e `routes/`, com `app.js` só fazendo bootstrap (Playbook T3).

### #3 [CRITICAL] Endpoint sensível sem autenticação/autorização (AP04)
File: src/AppManager.js:80, 131
Description: `GET /api/admin/financial-report` (linha 80) expõe receita por curso e nome de cada aluno, e `DELETE /api/users/:id` (linha 131) apaga qualquer usuário; nenhum dos dois tem middleware de autenticação ou autorização.
Impact: Qualquer cliente anônimo lê dados financeiros e pessoais e pode apagar a base de usuários um id por vez.
Recommendation: Criar middleware de autorização administrativa (token vindo de variável de ambiente) e aplicá-lo às rotas administrativas e de exclusão (Playbook T13).

### #4 [CRITICAL] Armazenamento inseguro de senha (AP05)
File: src/utils.js:17-23
src/AppManager.js:18, 68
Description: `badCrypto(pwd)` repete `Buffer.from(pwd).toString('base64').substring(0, 2)` 10000 vezes e corta em 10 caracteres: é base64 dos 2 primeiros caracteres repetido, sem salt e reversível. Em `AppManager.js:68`, `badCrypto(p || "123456")` atribui a senha padrão `123456` quando `pwd` não é enviado. O seed (linha 18) grava `'123'` em texto puro.
Impact: Senhas diferentes com o mesmo prefixo de 2 caracteres geram o mesmo "hash"; quem lê a tabela `users` recupera o início da senha, e contas criadas sem `pwd` têm senha conhecida por todos.
Recommendation: Usar `crypto.scrypt` com salt aleatório (biblioteca padrão do Node), não inventar senha padrão e gravar o seed já com hash (Playbook T5).

### #5 [CRITICAL] Exposição de dados sensíveis em log (AP06)
File: src/AppManager.js:45
Description: `console.log(\`Processando cartão ${cc} na chave ${config.paymentGatewayKey}\`)` grava o número completo do cartão e a chave live do gateway na saída padrão a cada checkout.
Impact: Logs passam a conter PAN de cartão e credencial de pagamento (violação de PCI-DSS); qualquer pessoa com acesso aos logs consegue usar a chave e os cartões.
Recommendation: Remover o log sensível e registrar apenas evento + id da matrícula via logger; se precisar identificar o cartão, logar só os 4 últimos dígitos (Playbook T5, T14).

### #6 [HIGH] Regra de negócio no controller/rota (Fat Controller) (AP07)
File: src/AppManager.js:28-78, 80-129, 131-137
Description: O handler de `POST /api/checkout` decide aprovação do pagamento (`cc.startsWith("4") ? "PAID" : "DENIED"`, linha 46), cria usuário, matrícula, pagamento e audit log com `this.db.run(...)` direto na rota. O handler do relatório (80-129) faz a agregação de receita (`courseData.revenue += payment.amount`, linha 109) e monta o DTO inline. O `DELETE` (131-137) chama o driver diretamente.
Impact: Regras de pagamento e de faturamento só podem ser testadas via HTTP; não há reaproveitamento das regras em outro canal (fila, CLI).
Recommendation: Extrair `checkoutService`, `reportService` e `userService`, deixando controllers só com leitura da requisição e montagem da resposta (Playbook T6).

### #7 [HIGH] Acoplamento forte sem injeção de dependência (AP08)
File: src/AppManager.js:1-2, 7
src/app.js:2-3, 8-10
Description: O construtor de `AppManager` instancia a dependência concreta `new sqlite3.Database(':memory:')` (linha 7) e importa `config`/`logAndCache`/`badCrypto` diretamente de `./utils` (linha 2). `app.js` só consegue usar essa conexão interna (`new AppManager()`, linha 8).
Impact: Impossível trocar o banco (arquivo, Postgres) ou injetar um mock em testes sem monkeypatch do módulo `sqlite3`.
Recommendation: Criar o banco em `database/` e passá-lo para models/services por parâmetro (factory `createApp({ db })`) (Playbook T7).

### #8 [HIGH] Estado global mutável (AP09)
File: src/utils.js:9-10, 14, 25
src/AppManager.js:2, 59
Description: `let globalCache = {}` e `let totalRevenue = 0` são variáveis de módulo exportadas; `logAndCache` muta `globalCache[key] = data` a cada checkout (chamado em `AppManager.js:59` com `last_checkout_${userId}`). `totalRevenue` é exportado e importado (`AppManager.js:2`) mas nunca atualizado, e por ser primitivo a cópia exportada nunca refletiria mudanças.
Impact: Cache cresce sem limite (um item por usuário), não é compartilhado entre instâncias e qualquer módulo pode alterá-lo; leva a vazamento de memória e a estado divergente entre processos.
Recommendation: Remover o cache global (não é lido em lugar algum) e o contador; se houver necessidade real de cache, encapsulá-lo em um serviço injetado (Playbook T7).

### #9 [HIGH] Operação multi-etapa sem transação / callback hell (AP10)
File: src/AppManager.js:37-76, 57, 83-127, 92, 104, 106, 133
Description: Checkout encadeia `db.get` → `db.get` → `db.run(users)` → `db.run(enrollments)` → `db.run(payments)` → `db.run(audit_logs)` em 6 níveis sem `BEGIN/COMMIT/ROLLBACK`. O usuário é inserido (linha 69) antes da verificação do pagamento, então um cartão recusado (linha 48) deixa o usuário gravado; falha no INSERT de `payments` (linha 55) deixa matrícula sem pagamento. Erros são ignorados em 57 (audit log), 92 (`enrollments.length` sobre `undefined` derruba o processo), 104, 106 e 133. O relatório usa contadores manuais `coursesPending`/`enrPending` (86, 93, 117-121) para saber quando responder.
Impact: Escritas parciais deixam o banco inconsistente (matrícula sem pagamento, usuário sem compra) e um erro de banco no relatório lança exceção fora do Express e derruba o servidor.
Recommendation: Envolver o driver em Promises, reescrever os fluxos com `async/await` e executar checkout dentro de transação única (`BEGIN`/`COMMIT`/`ROLLBACK`) (Playbook T9).

### #10 [MEDIUM] Configuração insegura de execução (AP11)
File: src/utils.js:6
src/AppManager.js:7
Description: Porta fixa `port: 3000` no objeto `config` e caminho do banco fixo `':memory:'` no construtor. Severidade reduzida de HIGH para MEDIUM porque não há `debug` exposto nem CORS aberto: o impacto se limita a não conseguir configurar o ambiente.
Impact: Não é possível subir duas instâncias na mesma máquina nem apontar para um banco persistente sem editar o código.
Recommendation: Ler `PORT` e `DB_PATH` de `process.env` em `config/` com defaults de desenvolvimento (Playbook T1).

### #11 [MEDIUM] Queries N+1 (AP12)
File: src/AppManager.js:83, 92, 104, 106
Description: O relatório faz `SELECT * FROM courses` (83), depois `SELECT * FROM enrollments WHERE course_id = ?` para cada curso (92) e, para cada matrícula, `SELECT name, email FROM users WHERE id = ?` (104) e `SELECT amount, status FROM payments WHERE enrollment_id = ?` (106): 1 + C + 2E queries.
Impact: Com 100 cursos e 10 mil matrículas são mais de 20 mil queries por requisição ao relatório.
Recommendation: Uma única query com `LEFT JOIN` entre courses, enrollments, users e payments e agregação em memória no service (Playbook T8).

### #12 [MEDIUM] Validação ausente ou fraca (AP13)
File: src/AppManager.js:29-35, 46, 132
Description: A única validação é `if (!u || !e || !cid || !cc)` (linha 35): não verifica tipo nem formato. Um `card` numérico (ex.: `4111222233334444` sem aspas) passa e `cc.startsWith("4")` (linha 46) lança `TypeError` dentro de um callback do sqlite3, fora do Express, derrubando o processo. `c_id` e o `:id` do DELETE (132) não são validados como inteiros e `eml` não tem checagem de formato.
Impact: Um único payload malformado derruba a API para todos; dados inválidos chegam ao banco.
Recommendation: Criar validador do payload de checkout (tipos string/inteiro, e-mail, cartão só dígitos) e do parâmetro `id`, respondendo 400 (Playbook T10).

### #13 [MEDIUM] Error handling inconsistente (AP14)
File: src/AppManager.js:35, 38, 41, 48, 51, 55, 70, 84, 135
src/app.js:5-10
Description: Erros respondidos em texto puro com mensagens diferentes (`res.status(400).send("Bad Request")`, `"Erro DB"`, `"Erro Matrícula"`, `"Erro Pagamento"`) enquanto o sucesso é JSON; `if (err || !course)` (38) transforma erro de banco em 404. O `DELETE` (135) responde 200 mesmo se houver erro ou se o usuário não existir. `app.js` não registra middleware de erro `(err, req, res, next)`.
Impact: Clientes não conseguem tratar erros de forma uniforme; falhas de banco são mascaradas como "não encontrado" ou "sucesso".
Recommendation: Criar classe `AppError` com status, middleware central de erro e handler 404; services lançam erros e controllers repassam via `next` (Playbook T4).

### #14 [MEDIUM] Código duplicado (AP15)
File: src/AppManager.js:96-98, 119-121
src/AppManager.js:41, 84
Description: O bloco de finalização `report.push(courseData); coursesPending--; if (coursesPending === 0) res.json(report);` aparece duas vezes (96-98 e 119-121); a resposta `res.status(500).send("Erro DB")` é repetida em 41 e 84.
Impact: Correções no fluxo de conclusão do relatório precisam ser feitas em dois lugares; fácil esquecer um e responder duas vezes ou nunca.
Recommendation: Com a query única e o error handler central, a lógica de conclusão e a resposta de erro existem em um só lugar (Playbook T6, T10).

### #15 [MEDIUM] Uso de APIs deprecated (AP16)
File: src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133
Description: Todo acesso a dados usa a API só de callback do `sqlite3` (`this.db.get(sql, params, (err, row) => ...)`, `this.db.run(..., function(err) { this.lastID })`), listada no catálogo como legada frente a wrapper com Promise / `async/await`.
Impact: Força callback hell (#9), impede `try/catch` e faz exceções escaparem do Express.
Recommendation: Criar wrapper com Promise (`run`/`get`/`all` retornando Promise, `run` devolvendo `lastID`/`changes`) usando só o driver atual (Playbook T11).

### #16 [MEDIUM] Integridade referencial ignorada (AP17)
File: src/AppManager.js:12-16, 133-135
Description: `DELETE FROM users WHERE id = ?` (133) não trata `enrollments` e `payments` do usuário, e a própria resposta admite: `"Usuário deletado, mas as matrículas e pagamentos ficaram sujos no banco."` (135). O schema (12-16) não declara `FOREIGN KEY` entre users/enrollments/payments.
Impact: Matrículas e pagamentos órfãos continuam somando receita no relatório financeiro com aluno `'Unknown'`.
Recommendation: Declarar `FOREIGN KEY ... ON DELETE CASCADE`, habilitar `PRAGMA foreign_keys = ON` e apagar dependentes na mesma transação (Playbook T9).

### #17 [LOW] Magic numbers / strings (AP18)
File: src/utils.js:19, 22
src/AppManager.js:21, 37, 46, 48, 68, 108
Description: `10000` iterações e `substring(0, 10)` em `badCrypto`; status `'PAID'`/`'DENIED'` repetidos como literais (21, 46, 48, 108); prefixo de cartão aprovado `"4"` (46); senha padrão `"123456"` (68); `active = 1` (37).
Impact: Regras de aprovação e status espalhados; mudar um status exige caçar strings.
Recommendation: Centralizar constantes (`PAYMENT_STATUS`, `APPROVED_CARD_PREFIX`) em um módulo de constantes/model (Playbook T12).

### #18 [LOW] Nomes ruins / pouco descritivos (AP19)
File: src/AppManager.js:4, 26, 29-33
src/utils.js:17
Description: Variáveis de uma letra/abreviadas `u`, `e`, `p`, `cid`, `cc` (29-33), `self` (26) para contornar `this`; classe genérica `AppManager` (4); função `badCrypto` (utils.js:17); arquivo `utils` guardando config. Os campos da API (`usr`, `eml`, `pwd`, `c_id`, `card`) também são abreviados, mas fazem parte do contrato público.
Impact: Leitura difícil e nomes que não dizem o papel real do código.
Recommendation: Renomear internamente (`name`, `email`, `password`, `courseId`, `cardNumber`), mantendo os nomes dos campos do contrato HTTP (Playbook T12).

### #19 [LOW] Código morto (AP20)
File: src/utils.js:2-3, 5, 9-10, 25
src/AppManager.js:2, 104
Description: `config.dbUser`, `config.dbPass` e `config.smtpUser` nunca são lidos; `globalCache` é exportado e nunca lido; `totalRevenue` é exportado (utils.js:25) e importado em `AppManager.js:2` sem uso; `SELECT name, email` (104) busca `email`, que não é usado.
Impact: Ruído que confunde quem mantém o código e mantém segredos sem utilidade no repositório.
Recommendation: Remover variáveis, exports e colunas não usados (Playbook T12).

### #20 [LOW] console.log como log (AP21)
File: src/utils.js:13
src/app.js:13
src/AppManager.js:45
Description: `console.log(\`[LOG] Salvando no cache: ${key}\`)`, `console.log(\`Frankenstein LMS rodando na porta ${config.port}...\`)` e o log de cartão (#5) usam `console.log` direto, sem nível nem formato.
Impact: Sem níveis (info/error), impossível filtrar ou silenciar logs por ambiente.
Recommendation: Criar um logger mínimo com níveis em `utils/logger` e usá-lo no lugar de `console.log` (Playbook T14).

## Deprecated APIs
- #15 API só de callback do `sqlite3` (`db.get/all/run(sql, params, cb)`) → wrapper com Promise / `async/await` (src/AppManager.js:37, 40, 50, 54, 57, 69, 83, 92, 104, 106, 133)
- Verificados e não encontrados: `new Buffer()` (o código usa `Buffer.from`, src/utils.js:20), `crypto.createCipher`, `url.parse()`, `body-parser` (usa `express.json()`, src/app.js:6), `res.send(status)`, `app.del()`, `req.param()`.

## Architecture Notes
Arquitetura atual: God Class. `app.js` é só bootstrap, mas `AppManager.js` concentra conexão, schema/seed, rotas, regras de pagamento/relatório e respostas, e `utils.js` mistura config com segredos, estado global e hash caseiro. Não há SQL Injection (todas as queries usam placeholders `?`), o que será preservado.
Direção: `config/` (env), `database/` (conexão Promise + schema/seed), `models/` (users, courses, enrollments, payments, audit_logs), `services/` (checkout com transação, relatório com JOIN, usuários), `controllers/`, `routes/` (views JSON), `middlewares/` (auth admin, validação, erro central). Contrato público (métodos, paths, campos `usr/eml/pwd/c_id/card`, chaves `msg/enrollment_id` e formato do relatório) será mantido; `npm start` continua sendo o comando de execução.

================================
Total: 20 findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
