# SolarFlow CRM v2

SolarFlow CRM is now a Django-based internal CRM for small solar installation teams. It adds secure login, server-backed lead data, activity history, CSV import, role-aware access, and a more professional office-facing interface.

## Stack

- Python 3.12
- Django 5.2.1
- SQLite for local development
- Django templates + static CSS

## Features

- Secure staff login with Django auth
- Manager vs staff access rules
- Manual lead creation
- CSV lead import
- Pipeline tracking across solar-specific stages
- Overdue and stuck lead visibility
- Customer timeline with activity logging
- Django admin as a safe back-office fallback

## Local run

On a normal development machine:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py seed_demo
python manage.py runserver
```

On this Codex workspace, Python is bundled and Django is unpacked in `vendor`, so this also works:

```powershell
$env:PYTHONPATH="C:\Users\recep\OneDrive\Documents\New project\vendor"
& "C:\Users\recep\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" manage.py migrate
& "C:\Users\recep\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" manage.py seed_demo
& "C:\Users\recep\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe" manage.py runserver
```

Then open `http://127.0.0.1:8000`.

## Demo accounts

- Manager: `mia` / `demo12345`
- Staff: `ava` / `demo12345`
- Staff: `noah` / `demo12345`

## CSV columns

Supported CSV headers:

- `name`
- `phone`
- `email`
- `address`
- `source`
- `stage`
- `notes`

Also supported: `customer`, `customer_name`, `mobile`, `lead_source`, `suburb`.
