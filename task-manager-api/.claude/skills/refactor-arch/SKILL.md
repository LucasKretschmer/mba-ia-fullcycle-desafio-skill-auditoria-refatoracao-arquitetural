---
name: refactor-arch
description: Audita e refatora um projeto backend legado para o padrão MVC. Detecta stack e arquitetura, cruza o código com um catálogo de anti-patterns (segurança, SOLID, MVC, performance, APIs deprecated), gera relatório de auditoria com arquivo/linha e severidade, pede confirmação e então reestrutura o projeto validando boot e endpoints. Use quando pedirem auditoria arquitetural, refatoração para MVC ou limpeza de code smells em qualquer linguagem/framework.
disable-model-invocation: true
---

# refactor-arch

Você vai atuar como um arquiteto de software revisando um projeto legado que acabou de herdar.
O trabalho é dividido em **3 fases sequenciais**. Não pule fases e não altere nenhum arquivo antes da confirmação no fim da Fase 2.

Arquivos de referência (leia cada um quando a fase pedir, não antes):

| Arquivo | Usado em | Conteúdo |
|---|---|---|
| `references/project-analysis.md` | Fase 1 | Heurísticas para detectar linguagem, framework, banco, domínio e arquitetura |
| `references/anti-patterns-catalog.md` | Fase 2 | Catálogo de anti-patterns com sinais de detecção e severidade |
| `references/report-template.md` | Fase 2 | Formato obrigatório do relatório de auditoria |
| `references/mvc-guidelines.md` | Fase 3 | Estrutura MVC alvo e responsabilidade de cada camada |
| `references/refactoring-playbook.md` | Fase 3 | Transformações concretas (antes/depois) para cada anti-pattern |

Regras gerais:

- O diretório atual (onde a skill foi chamada) é a raiz do projeto alvo. Ignore `.claude/`, `node_modules/`, `venv/`, `.venv/`, `__pycache__/`, `.git/`, arquivos `*.db` e lockfiles na contagem de arquivos.
- Seja agnóstico de tecnologia: as regras valem para qualquer linguagem. Os exemplos das referências são Python e JavaScript, adapte a sintaxe para a stack detectada.
- Toda afirmação sobre o código precisa de evidência (arquivo e linha). Nunca invente linhas: use a ferramenta de leitura com numeração ou `grep -n` para confirmar.
- Escreva o código novo no estilo do projeto (idioma dos nomes, aspas, indentação). Comentários só quando o "porquê" não for óbvio.

---

## Fase 1 — Análise do projeto

1. Leia `references/project-analysis.md`.
2. Liste os arquivos do projeto e leia **todos** os arquivos de código-fonte e de dependências (`requirements.txt`, `package.json`, `pyproject.toml`, `go.mod`, `pom.xml` etc.).
3. Determine: linguagem, framework (com versão do manifesto), dependências relevantes, banco de dados, domínio da aplicação, arquitetura atual, quantidade de arquivos de código e tabelas/entidades.
4. Monte o **inventário de endpoints** (método + path + arquivo:linha do handler). Ele será usado na validação da Fase 3.
5. Imprima o resumo exatamente neste formato:

```
================================
PHASE 1: PROJECT ANALYSIS
================================
Language:      <linguagem + versão se conhecida>
Framework:     <framework + versão>
Dependencies:  <libs relevantes, separadas por vírgula>
Database:      <engine + forma de acesso (driver cru, ORM...)>
Domain:        <descrição curta do domínio + entidades principais>
Architecture:  <classificação + justificativa em uma linha>
Source files:  <N> files analyzed (~<L> lines)
DB tables:     <tabelas/entidades>
Endpoints:     <N> endpoints mapeados
================================
```

Em seguida imprima o inventário de endpoints como tabela (`Method | Path | Handler`).

Siga direto para a Fase 2.

---

## Fase 2 — Auditoria

1. Leia `references/anti-patterns-catalog.md` e `references/report-template.md`.
2. Percorra **cada arquivo** de código e cruze com **cada item** do catálogo usando os sinais de detecção. Use `grep -n` para os sinais textuais (ex.: concatenação em SQL, `password`, `secret`, `debug=True`, `print(`, `console.log`, `.query.get(`, `utcnow`) e leitura completa para os sinais estruturais (God Class, lógica em controller, N+1).
3. Para cada ocorrência registre: ID do catálogo, severidade, arquivo, linha(s) exata(s), descrição específica do caso (cite o trecho), impacto e recomendação (referencie a transformação do playbook, ex.: `Playbook T2`).
   - Mesmo problema em vários lugares do mesmo tipo: um finding só, listando todas as localizações.
   - Verifique explicitamente APIs deprecated da stack (seção "APIs deprecated" do catálogo). Se não houver nenhuma, diga isso no relatório.
4. Ordene os findings por severidade: CRITICAL → HIGH → MEDIUM → LOW.
5. Gere o relatório seguindo **exatamente** `references/report-template.md` e imprima no terminal.
6. Salve o relatório em `reports/audit-report.md` dentro do projeto (crie a pasta se não existir). Esse é o único arquivo que pode ser criado antes da confirmação.
7. Termine com a pergunta abaixo e **PARE**. Aguarde a resposta do usuário.

```
Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

- Resposta `n` (ou qualquer coisa diferente de confirmação): encerre sem modificar nada.
- Se o usuário pedir para ignorar algum finding, registre e respeite na Fase 3.

---

## Fase 3 — Refatoração

Só execute após confirmação explícita.

1. Leia `references/mvc-guidelines.md` e `references/refactoring-playbook.md`.
2. **Baseline antes de mexer:** suba a aplicação original (veja "Como validar" em `references/project-analysis.md`), chame cada endpoint do inventário e guarde status code + formato da resposta. Se a aplicação original não subir, registre o motivo e use o inventário estático como baseline.
3. **Plano:** defina a estrutura alvo conforme `mvc-guidelines.md`, adaptando ao nível de organização atual:
   - Projeto monolítico/desestruturado → criar a estrutura MVC completa.
   - Projeto já parcialmente em camadas → preservar o que já está certo, criar as camadas que faltam (ex.: controllers, config, middlewares) e mover responsabilidades para o lugar correto. Não reescreva por reescrever.
   Imprima a árvore planejada (`## Planned Structure`) **antes de editar o primeiro arquivo**. Ela serve de contrato para o resumo final.
   Se a remoção de arquivos legados for bloqueada por permissão, não contorne: liste os arquivos no resumo final e peça ao usuário para removê-los.
4. **Execute** as transformações do playbook para cada finding, na ordem: config/segredos → camada de dados (models, queries seguras) → controllers/services → views/rotas → error handling → entry point → itens MEDIUM/LOW restantes.
   - Preserve o **contrato público**: mesmos métodos, paths, status codes e chaves de resposta. Exceções aceitas apenas quando a própria correção de segurança exige (ex.: não devolver hash de senha, proteger endpoint administrativo). Liste cada exceção como "mudança intencional de comportamento".
   - Preserve o comando de execução original (ex.: `python app.py`, `npm start`). Se o entry point mudar de lugar, mantenha um shim no local antigo.
   - Segredos vão para variáveis de ambiente com fallback seguro apenas para desenvolvimento; crie `.env.example` documentando as variáveis.
   - Remova os arquivos antigos que ficaram vazios ou viraram código morto.
   - Atualize o manifesto de dependências se adicionar libs (prefira a biblioteca padrão quando ela resolve).
5. **Validação** (obrigatória, não declare sucesso sem rodar):
   1. Instale dependências se necessário e suba a aplicação com o comando original. Ela deve iniciar sem erros nem warnings de import.
   2. Chame **todos** os endpoints do inventário (curl ou script) e compare com o baseline: mesmo status code e mesmas chaves no corpo, salvo as mudanças intencionais.
   3. Teste ao menos um caminho de erro (ex.: recurso inexistente → 404, payload inválido → 400) para provar que o error handler centralizado funciona.
   4. Refaça a varredura do catálogo nos arquivos novos. Todo CRITICAL e HIGH deve estar resolvido; se algum item ficar pendente, explique por quê.
   5. Pare o servidor ao terminar e apague bancos/arquivos temporários criados só para o teste.
   Se algo falhar, corrija e valide de novo. Não pule a validação.
6. Imprima o resumo final:

```
================================
PHASE 3: REFACTORING COMPLETE
================================
## New Project Structure
<árvore de diretórios>

## Changes Applied
- <ID finding> → <o que foi feito> (Playbook Tn)
...

## Intentional Behavior Changes
- <mudança e motivo>   (ou "None")

## Validation
  ✓ Application boots without errors (<comando>)
  ✓ <N>/<N> endpoints respond as baseline
  ✓ Centralized error handling verified (<exemplo>)
  ✓ No CRITICAL/HIGH anti-patterns remaining
================================
```

Use `✗` no lugar de `✓` para qualquer item que não passou e explique logo abaixo.
