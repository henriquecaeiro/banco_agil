# Contribuindo com o Banco Ágil

## Branches

- `master`: versão estável e validada.
- `test`: integração das alterações antes da publicação.
- `feat/*`: novas funcionalidades.
- `fix/*`: correções de defeitos.
- `chore/*`: manutenção e configuração.
- `docs/*`: documentação.
- `qa/*`: testes e hardening.

Toda alteração parte de `test`, passa pelos testes na branch de implementação e retorna a
`test` com merge explícito. Somente uma `test` estável é integrada em `master`.

```text
feat/*, fix/*, docs/*, chore/* ou qa/*
                    ↓
                   test
                    ↓
                  master
```

## Validação

Antes do merge, execute:

```bash
pytest -q
ruff check .
```

## Commits

Use Conventional Commits e descreva uma mudança real e coesa:

```text
feat: add ...
fix: handle ...
test: cover ...
docs: document ...
chore: configure ...
refactor: simplify ...
```

Em um projeto de equipe, branches concluídas normalmente podem ser removidas após o merge. Neste
repositório de portfólio, algumas branches são mantidas para tornar o fluxo de desenvolvimento
visível.
