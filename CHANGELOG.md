# Changelog

## [0.2.2](https://github.com/levyvix/comando_cli/compare/v0.2.1...v0.2.2) (2026-04-21)


### Bug Fixes

* **update:** detect latest version across tags and pyproject ([9857b8a](https://github.com/levyvix/comando_cli/commit/9857b8aa0ca4b4697b7a9bdad402355f0ebc7ad2))

## [0.2.1](https://github.com/levyvix/comando_cli/compare/v0.2.0...v0.2.1) (2026-04-21)


### Bug Fixes

* **installer:** install from temp repo clone instead of cwd ([b148a30](https://github.com/levyvix/comando_cli/commit/b148a308d69c529320fa590c2d1417a1a635466f))

## [0.2.0](https://github.com/levyvix/comando_cli/compare/v0.1.0...v0.2.0) (2026-04-21)


### Features

* Add core streaming CLI infrastructure with tests ([2b66e71](https://github.com/levyvix/comando_cli/commit/2b66e71e0c56e8168489b5da35750eefa38bce4a))
* add fzf title selection and improve series/episode handling ([35190ee](https://github.com/levyvix/comando_cli/commit/35190eead14d2bf9bee53671c9bb5205c536bee6))
* **cli:** add update/version commands and release bump workflow ([8cbb01a](https://github.com/levyvix/comando_cli/commit/8cbb01a544349ad9f7e600ee73025a6f543d4649))
* default episode range to 1- (play all from first) when unspecified ([63ed912](https://github.com/levyvix/comando_cli/commit/63ed9120925cd0b6a5af0c592d73757e7f298b51))
* improve playback selection flow and add scraper caching ([69841d2](https://github.com/levyvix/comando_cli/commit/69841d2063eddaf9a4d748230a32d26a01814d5e))
* **playback:** auto-cleanup webtorrent temp files after each session ([d56e7ee](https://github.com/levyvix/comando_cli/commit/d56e7eecd318fad5179e09a227c3d80fb2e1f111))
* save title_url and magnet_url in watch history ([2e1b623](https://github.com/levyvix/comando_cli/commit/2e1b6230bb6e9b29ddf1f9f911b269c9f5c59e5b))
* set up yoyo migrations system for database schema management ([d554a0f](https://github.com/levyvix/comando_cli/commit/d554a0fe828fee196e7231e92b8ef60d714d7001))
* support consolidated torrents with per-episode playlist streaming ([fe66441](https://github.com/levyvix/comando_cli/commit/fe66441e6c76ba9cf6dfa1aef2b38762bb3a7011))
* support multi-episode group magnets (e.g. E01-02-03) ([79e59fc](https://github.com/levyvix/comando_cli/commit/79e59fce650197a9abeb2c6aeda24249a91c3d9d))


### Bug Fixes

* prevent title mutation when filtering quality options by episode ([eb75bb1](https://github.com/levyvix/comando_cli/commit/eb75bb10081f75935c789bd4ea3d69539c550cbe))
* update scraper tests to match actual HTML structure and mock setup ([#1](https://github.com/levyvix/comando_cli/issues/1)) ([5a9a4b2](https://github.com/levyvix/comando_cli/commit/5a9a4b2d60eed802373ee1009ecb9b65e96462ed))


### Documentation

* Add comprehensive README with installation and dependencies ([9557ffd](https://github.com/levyvix/comando_cli/commit/9557ffddd6b58cc7fef230d57e481754ea1023ff))
* simplify installation and usage instructions ([c672c48](https://github.com/levyvix/comando_cli/commit/c672c489dc39a55fef94c37fb3285c09843e65f1))
* Update final testing phase summary ([fd34753](https://github.com/levyvix/comando_cli/commit/fd3475392d71ecb36368d9a9f5622f4203a0dbab))
* Update task completion status for testing phase ([f2755b3](https://github.com/levyvix/comando_cli/commit/f2755b31833774ffb52e53e93b499a8576185c85))
