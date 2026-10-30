# TODO

- [x] Add Company "status", which indicates our relationship with them: Prospekt
  or Kund (NULL is shown as Okänd).
- [x] Filter companies by status; add a filter to the company list where you can search by status.
- [ ] Support soft-delete for companies; use the same solution as for Leads
- [ ] Support soft-delete for candidates; use the same solution as for Leads
- [ ] "Quick navigation", like Ctrl+P in VSCode. Add a generic search bar at
  the top of the navbar where you can search for both companies and candidates.
  As the user types, matches are fetched from the server as "autocomplete"
  suggestions; clicking on a match opens that candidate or company. Use
  Bootstrap Icons to distinguish between companies (city icon) and candidates
  (person icon). Pressing Enter opens the first match suggestion.
