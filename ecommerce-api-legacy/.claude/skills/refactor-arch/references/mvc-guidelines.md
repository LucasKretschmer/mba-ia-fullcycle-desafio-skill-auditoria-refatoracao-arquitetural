# Guidelines de Arquitetura — MVC Alvo

Padrão alvo da Fase 3. Em uma API REST não há template HTML, então a **View** é a camada de apresentação HTTP: mapeamento de rotas e formatação da resposta (JSON).

## Camadas e responsabilidades

| Camada | Responsabilidade | Pode depender de | Não pode |
|---|---|---|---|
| **config** | Ler variáveis de ambiente, defaults de desenvolvimento, constantes da aplicação | nada | ter lógica de negócio, segredos literais de produção |
| **models** | Entidades, schema, acesso a dados (queries parametrizadas / ORM) e regras que pertencem à entidade (`is_overdue`, `calcular_total`) | database, config | importar framework HTTP, ler `request`, devolver `Response` |
| **services** *(opcional)* | Casos de uso que envolvem várias entidades ou efeitos externos (checkout, relatório agregado, notificação) | models, config | conhecer HTTP |
| **controllers** | Fluxo de cada requisição: extrair e validar entrada, chamar model/service, escolher status code, delegar formatação à view | models, services, validators, views | montar SQL, ter regra de negócio pesada, `try/except` genérico em cada função |
| **views / routes** | Registrar rotas (método + path → controller) e serializar a saída (`to_dict`, presenter, `jsonify`) | controllers | acessar banco, validar regra de negócio |
| **middlewares** | Error handler central, autenticação/autorização, logging de requisição | config | regra de negócio |
| **entry point** | Composition root: cria app, carrega config, inicializa banco, injeta dependências, registra rotas e middlewares, sobe o servidor | todas | ter rota ou regra |

Fluxo de dependência (sempre em um sentido só):

```
request → views/routes → controllers → services → models → database
                 ↑                                   ↑
             middlewares                           config
```

Regra prática: se você trocar Flask por FastAPI (ou Express por Fastify), só `views/`, `middlewares/` e o entry point deveriam mudar.

## Estrutura alvo

Python (Flask):

```
<projeto>/
├── app.py                      # entry point fino (mantém `python app.py`)
├── requirements.txt
├── .env.example
└── src/
    ├── __init__.py
    ├── app.py                  # create_app(): composition root
    ├── config/
    │   └── settings.py
    ├── database.py             # conexão / sessão / init de schema
    ├── models/
    │   └── <entidade>_model.py
    ├── services/               # se houver caso de uso multi-entidade
    │   └── <caso>_service.py
    ├── controllers/
    │   └── <entidade>_controller.py
    ├── views/
    │   └── <entidade>_routes.py
    ├── middlewares/
    │   ├── error_handler.py
    │   └── auth.py             # se houver endpoint protegido
    └── utils/
        └── validators.py
```

Node.js (Express):

```
<projeto>/
├── package.json                # "start" continua funcionando
├── .env.example
└── src/
    ├── app.js                  # composition root + listen
    ├── config/
    │   └── settings.js
    ├── database/
    │   └── connection.js       # conexão, schema, seed, helpers async
    ├── models/
    │   └── <entidade>Model.js
    ├── services/
    │   └── <caso>Service.js
    ├── controllers/
    │   └── <entidade>Controller.js
    ├── views/
    │   └── routes.js           # express.Router()
    ├── middlewares/
    │   ├── errorHandler.js
    │   └── auth.js
    └── utils/
        └── validators.js
```

Nomes de arquivo seguem a convenção da linguagem (`snake_case` em Python, `camelCase` em JS). Agrupe por domínio: um model, um controller e um arquivo de rotas por entidade principal. Não crie arquivos vazios só para "completar" a árvore.

## Adaptação ao nível de organização

**Projeto monolítico / God Class:** criar a estrutura completa acima. Quebrar o arquivo gigante por domínio (produtos, usuários, pedidos...) e por camada.

**Projeto já em camadas parciais** (ex.: já tem `models/`, `routes/`, `services/`, `utils/` na raiz):
- Mantenha os diretórios existentes no lugar se estiverem corretos; não mova tudo para `src/` só por estética.
- `routes/` passa a ser a camada de **views**: só registra Blueprints/Routers e chama controllers. Pode manter o nome `routes/`, desde que cumpra esse papel.
- Crie o que falta: `controllers/`, `config/`, `middlewares/`.
- Mova regra de negócio das rotas para models (regras da entidade) ou services (agregações, relatórios).
- Aproveite helpers existentes que estavam mortos (ex.: validações prontas em `utils/` que ninguém chamava) em vez de duplicar.

## Regras obrigatórias

1. **Config:** nenhum segredo literal. `SECRET_KEY`, senhas, chaves de gateway, URL do banco, `DEBUG`, porta e origens de CORS vêm do ambiente. Default de desenvolvimento só para valores não sensíveis; para segredos, gere um valor aleatório em dev e logue um aviso.
2. **Debug** desligado por padrão (`DEBUG=false` a menos que o ambiente diga o contrário).
3. **Error handling centralizado:** um único lugar converte exceções em resposta. Controllers lançam erros de domínio (`NotFoundError`, `ValidationError`) em vez de montar 404/400 manualmente em todo lugar. Erros inesperados → 500 com mensagem genérica, detalhe só no log.
4. **Formato de erro estável:** use a mesma chave que o projeto já usava (`erro` ou `error`) para não quebrar clientes.
5. **Models nunca recebem `request`** e nunca devolvem objetos de resposta HTTP.
6. **Queries sempre parametrizadas.** Operações multi-etapa dentro de transação.
7. **Serialização em um lugar só** (`to_dict` / presenter); dados sensíveis (senha, hash) nunca saem na resposta.
8. **Entry point claro:** o comando de execução original continua funcionando; `create_app()` / composition root explícito, sem efeitos colaterais no import (exceto o que o framework exige).
9. **Logging** pelo módulo de log da linguagem (`logging`, `console.error` centralizado ou lib), nunca registrando senha ou cartão.
10. **Sem código morto:** apague arquivos antigos substituídos e imports sem uso.

## Checklist de saída da Fase 3

- [ ] Estrutura de diretórios segue o padrão MVC
- [ ] Configuração extraída para módulo de config (sem hardcoded)
- [ ] Models abstraem os dados
- [ ] Views/Routes separadas e finas
- [ ] Controllers concentram o fluxo da aplicação
- [ ] Error handling centralizado
- [ ] Entry point claro
- [ ] Aplicação inicia sem erros
- [ ] Endpoints originais respondem corretamente
