# AGENTS

## Commit Policy

Use Conventional Commits for all commits so the automated version bump workflow can determine release type.

Required format:

```
<type>(<scope>): <subject>
```

Examples:

- `feat(cli): add update check`
- `fix(scraper): handle empty search results`
- `chore(ci): adjust version bump workflow`

Version bump mapping used by `.github/workflows/bump-version.yml`:

- `major`: commit contains `BREAKING CHANGE` or `!` in type/scope, e.g. `feat(api)!: change response format`
- `minor`: commit type `feat`
- `patch`: all other commit types (`fix`, `chore`, `docs`, `refactor`, etc.)
