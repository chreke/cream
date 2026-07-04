# Spec 002: Base template and site structure

Status: Done (2026-07-04)

Layout is loosely based on the prototype in `Design.png` (dark sidebar, cream
content area, magenta accent) — it's a prototype, not a pixel-exact target.

## Decisions

- **Bootstrap 5.3.8 vendored** into `static/vendor/` (CSS + JS bundle), no
  build step. Theming is done by overriding Bootstrap's CSS variables in
  `static/css/cream.css`.
- **Theme colors** (gleaned from the prototype):
  - `--cream-dark`: `#12141f` — sidebar / dark surfaces
  - `--cream-bg`: `#faf6f1` — content background
  - `--cream-accent`: `#e6127d` — primary/brand magenta
- **System fonts** for both headings and body (no vendored webfonts).
- **Sidebar nav** contains only the specced sections: Företag, Kandidater,
  Pipeline. Dashboard/Events/Inställningar from the prototype are omitted
  until specced.
- **No authentication yet.** The header shows a hardcoded placeholder user
  (TODO comment in the template); login/logout is a future task.
- **URLs and code in English, copy in Swedish**: `/companies/`,
  `/candidates/`, `/pipeline/` with Swedish page titles and nav labels.
- **`/` redirects to the companies list.**
- **List views are tables** (per REQUIREMENTS.md), not cards as in the
  prototype.

## Out of scope

- Login/logout and real user display
- Actual list content for companies/candidates/pipeline (placeholder pages
  extending the base template for now)
- Production static file serving. In development, `runserver` serves
  `/static/` automatically. For production, decide between reverse proxy
  serving `collectstatic` output vs. WhiteNoise — handled in the Deployment
  task.
