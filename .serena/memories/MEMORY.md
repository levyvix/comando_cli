## Projeto: comando-cli

**Descrição**: CLI Python para streaming de filmes e séries do gratistorrent.com

**Tech Stack**:
- Python 3.12+
- UV (package manager)
- OpenSpec (spec-driven development)
- Scrapling (web scraping com Cloudflare solve_cloudflare=True)
- webtorrent (streaming de torrents)
- mpv (player)
- fzf (busca interativa)
- Click (CLI framework)
- SQLite (watch history)
- Pydantic (data models)

**Estrutura do Projeto**:
- `main.py` - Entrypoint
- `src/comando_cli/` - Módulos principais
- `pyproject.toml` - Dependências
- `openspec/` - Especificações

**Git**: main branch é o branch principal

**Workflow**:
1. Criar proposta de spec em `openspec/changes/` ✅ FEITO: add-streaming-cli
2. Validar com `openspec validate [change-id] --strict` ✅ FEITO
3. Implementar conforme tasks.md
4. Arquivar após deploy

**Proposta Atual**: add-streaming-cli
- 4 capabilities: search, episode-selection, playback, watch-history
- Design.md com decisões arquiteturais
- Tasks.md com 9 fases de implementação
- Todos os spec.md validados

**Próximo Passo**: Aguardar aprovação do usuário para começar implementação
