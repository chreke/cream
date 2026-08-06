# Candidate Search

## Overview

Free-text search for the candidates list, backed by Postgres full-text
search, with results ranked by relevance. Replaces the `icontains` approach
used by the company list, which cannot rank results and cannot use an index.

## Requirements

### Matching

- A single free-text query input (`q`) on the candidates list page.
- The search targets **Name** and **Skills**. Location is handled by its own
  exact-match filter, and Description is deliberately excluded.
- Matching is **word-prefix based**: a query word matches the beginning of
  whole words (tokens) in the indexed fields. `java` matches both "Java" and
  "JavaScript". It does not provide arbitrary substring matching: `script`
  does not match "JavaScript".
- Matching is case-insensitive. No language stemming is applied (skills and
  names should match literally).
- **All query words must match** (AND semantics), either exactly or as a word
  prefix. Each word may match in either field: `sara python` finds candidates
  with "Sara" in the name and "Python" in skills.
- An empty or blank query returns all candidates.

### Ranking

- Search results are ordered by **relevance**, not name.
- Candidates matching every query term as an exact word rank ahead of
  candidates that require prefix matching. For example, `java` ranks "Java"
  ahead of "JavaScript". Exactness is scored once for the whole query.
- Both fields count equally toward relevance (no field weighting).
- Candidates with equal relevance are ordered by name (Swedish collation).
- Without a search query, candidates are ordered by name.

### Interaction with filters

- A Location dropdown contains the distinct, non-empty locations currently
  used by candidates. Selecting one applies an exact-match filter.
- The Location and Kind filters combine with search (all must hold). Filtering
  never affects ranking.
- Search and filter state must survive pagination links.

### Performance

- The search must be able to use a database index (GIN); it must not
  require a sequential scan over candidates.

## Out of scope (considered and deferred)

- **Substring, fuzzy and typo-tolerant matching**: `script` does not match
  "JavaScript", and misspellings are not corrected. These would require a
  separate trigram-based search strategy and index.
- **Upgrading company search**: the company list keeps its `icontains`
  search for now.
- **Searching Description**: cheap to add later at a low weight if needed.
