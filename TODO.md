# TODO

- [x] Simplify candidate exact-match ranking to score the whole query once
      ([spec](specs/006-candidate-search.md))
- [x] Add prefix matching to candidate search, with exact-word matches ranked
      ahead of prefix-only matches ([spec](specs/006-candidate-search.md))
- [ ] Transfer data from Candide ([spec](specs/015-candide-migration.md)):
      `import_candide` management command — dumpdata JSON + manually copied
      media, one-time cutover; candidates + CVs + comments, all comments/flags
      attributed to a single import user
