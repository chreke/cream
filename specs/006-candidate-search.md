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
- Matching is **word-based and exact**: a query word matches whole words
  (tokens) in the indexed fields. `java` matches "Java" but *not*
  "JavaScript"; `stockh` matches nothing. No prefix or substring matching.
- Matching is case-insensitive. No language stemming is applied (skills,
  names and places should match literally).
- **All query words must match** (AND semantics). Each word may match in any
  of the three fields: `python stockholm` finds candidates with "Python" in
  skills and "Stockholm" in location.
- An empty or blank query returns all candidates.

### Ranking

- Search results are ordered by **relevance**, not name.
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

- **Prefix / near-miss matching**: including "JavaScript" (ranked lower)
  in results for `java`, and matching partially typed words like `stockh`.
  Decided against to keep the first version simple; revisit if exact-word
  matching proves too strict in practice.
- **Upgrading company search**: the company list keeps its `icontains`
  search for now.
- **Searching Description**: cheap to add later at a low weight if needed.
