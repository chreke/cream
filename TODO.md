# TODO

- [x] Cap Skills table columns at 40 characters
- [x] Reject contact timestamps older than the Company's last contact
- [x] Move the new-comment input above the comment feed
- [x] Show total candidate and company counts in their list-page headers
- [x] Replace candidate location full-text search with an exact location
      dropdown filter ([spec](specs/006-candidate-search.md))
- [x] Simplify candidate exact-match ranking to score the whole query once
      ([spec](specs/006-candidate-search.md))
- [x] Add prefix matching to candidate search, with exact-word matches ranked
      ahead of prefix-only matches ([spec](specs/006-candidate-search.md))
- [ ] Differentiate contact-log comments from ordinary comments with a comment
      type and phone icon ([spec](specs/017-typed-contact-comments.md))
- [ ] Transfer data from Candide ([spec](specs/015-candide-migration.md)):
      `import_candide` management command — dumpdata JSON + manually copied
      media, one-time cutover; candidates + CVs + comments, all comments/flags
      attributed to a single import user
