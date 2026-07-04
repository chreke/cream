# Spec 003: Authentication

Status: Done (2026-07-04)

## Scope

- Login screen (Swedish copy), standalone page without the app sidebar.
- Logout via a dropdown menu on the user chip in the header; "Logga ut" is
  a menu item. Logout is a POST (Django 5 requires POST for LogoutView), so
  the menu item is a small form.
- All views require authentication.

## Decisions

- **All views require login via `LoginRequiredMiddleware`** (built into
  Django 5.1+) instead of adding `LoginRequiredMixin` to every view.
  Login/logout/admin-login are exempt automatically via
  `@login_not_required`.
- **Accounts are admin-managed.** A superuser creates users and resets
  passwords in the Django admin. No self-service signup, no
  "forgot password" email flow (and therefore no SMTP configuration).
- **Login with username** (Django default).
- **Default session length** (2 weeks).
- Django's built-in `LoginView`/`LogoutView` with a custom template at
  `templates/registration/login.html`.
- `crm.User` is registered in the Django admin (models should be in the
  admin by default, per CLAUDE.md).

## Out of scope

- Password reset via email
- User self-registration
- Roles/permissions (all users have all privileges, per REQUIREMENTS.md)
