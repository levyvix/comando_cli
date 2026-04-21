# AGENTS

## Commit Policy

Use Conventional Commits for all commits so the `release-please` workflow can determine release type.

Required format:

```
<type>(<scope>): <subject>
```

Examples:

- `feat(cli): add update check`
- `fix(scraper): handle empty search results`
- `chore(ci): adjust version bump workflow`

Release mapping used by `.github/workflows/release-please.yml`:

- `major`: commit contains `BREAKING CHANGE` or `!` in type/scope, e.g. `feat(api)!: change response format`
- `minor`: commit type `feat`
- `patch`: all other commit types (`fix`, `chore`, `docs`, `refactor`, etc.)
