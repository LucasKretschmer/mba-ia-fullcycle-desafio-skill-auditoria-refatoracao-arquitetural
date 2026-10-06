# Template do Relatório de Auditoria

O relatório da Fase 2 deve seguir **exatamente** a estrutura abaixo. Ele é impresso no terminal e salvo em `reports/audit-report.md`.

## Regras

1. Findings ordenados por severidade: todos os CRITICAL, depois HIGH, MEDIUM e LOW. Dentro da mesma severidade, ordene por ID do catálogo.
2. Numere os findings em sequência (`#1`, `#2`...). A numeração é usada como referência na Fase 3.
3. `File:` sempre com caminho relativo à raiz do projeto e linha(s) exatas: `models.py:28`, `models.py:47-50`. Se o problema aparece em vários pontos, liste todos separados por vírgula (`models.py:28, 92, 140`), ou um arquivo por linha quando forem arquivos diferentes.
4. `Description` cita o caso concreto (nome da função, variável, trecho curto do código). Nada genérico.
5. `Recommendation` diz o que fazer e aponta a transformação do playbook (`Playbook T2`).
6. O `Summary` precisa bater com a contagem real dos findings.
7. A seção `Deprecated APIs` é obrigatória: liste os findings AP16 ou escreva "Nenhuma API deprecated encontrada".
8. Termine com a pergunta de confirmação e pare.

## Estrutura

```markdown
================================
ARCHITECTURE AUDIT REPORT
================================
Project: <nome da pasta do projeto>
Stack:   <linguagem> + <framework versão>
Files:   <N> analyzed | ~<L> lines of code
Date:    <AAAA-MM-DD>

## Summary
CRITICAL: <n> | HIGH: <n> | MEDIUM: <n> | LOW: <n>

## Findings

### #1 [CRITICAL] <Nome do anti-pattern> (AP0X)
File: <arquivo>:<linha(s)>
Description: <o que foi encontrado, citando o código>
Impact: <consequência concreta para segurança/manutenção/performance>
Recommendation: <ação> (Playbook Tn)

### #2 [CRITICAL] ...

### #k [HIGH] ...

### #m [MEDIUM] ...

### #n [LOW] ...

## Deprecated APIs
- #<n> <API antiga> → <API moderna> (<arquivo>:<linha>)

## Architecture Notes
<2 a 5 linhas: diagnóstico geral da arquitetura atual e direção da refatoração (o que vai virar model, controller, view; o que será preservado)>

================================
Total: <N> findings
================================

Phase 2 complete. Proceed with refactoring (Phase 3)? [y/n]
```

## Exemplo de finding bem escrito

```markdown
### #2 [CRITICAL] SQL Injection (AP02)
File: models.py:28, 47-50, 57-61, 110, 140, 291
Description: Queries montadas por concatenação de strings com dados da requisição, ex.: `"SELECT * FROM usuarios WHERE email = '" + email + "' AND senha = '" + senha + "'"` em `login_usuario`.
Impact: Um payload como `' OR '1'='1` no e-mail autentica sem senha; permite ler e apagar qualquer tabela.
Recommendation: Usar placeholders `?` com tupla de parâmetros em todas as queries (Playbook T2).
```

## Exemplo de finding mal escrito (não faça)

```markdown
### [HIGH] Código ruim
File: models.py
Description: O código tem problemas de segurança.
```

Falta linha, ID, caso concreto, impacto e recomendação.
