# Candidate Search

## Overview

Free-text search for the candidates list, backed by Postgres full-text
search, with results ranked by relevance. Replaces the `icontains` approach
used by the company list, which cannot rank results and cannot use an index.

## Requirements

### Matching

- A single free-text query input (`q`) on the candidates list page.
- The search targets **Name**, **Location** and **Skills**. Description is
  deliberately excluded.
- Matching is **word-prefix based**: a query word matches the beginning of
  whole words (tokens) in the indexed fields. `java` matches both "Java" and
  "JavaScript", and `stockh` matches "Stockholm". It does not provide
  arbitrary substring matching: `script` does not match "JavaScript".
- Matching is case-insensitive. No language stemming is applied (skills,
  names and places should match literally).
- **All query words must match** (AND semantics), either exactly or as a word
  prefix. Each word may match in any of the three fields: `python stockh`
  finds candidates with "Python" in skills and "Stockholm" in location.
- An empty or blank query returns all candidates.

### Ranking

- Search results are ordered by **relevance**, not name.
- Exact-word matches rank ahead of prefix-only matches. Exactness is scored
  per query term, so `java stockh` ranks "Java" + "Stockholm" ahead of
  "JavaScript" + "Stockholm".
- All three fields count equally toward relevance (no field weighting).
- Candidates with equal relevance are ordered by name (Swedish collation).
- Without a search query, candidates are ordered by name.

### Interaction with filters

- The Kind filter combines with search (both must hold). Kind filtering
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
