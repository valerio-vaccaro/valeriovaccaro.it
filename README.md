# Personal Website (Flask + SQLite)

A multi-user personal website where each logged user can manage:
- Profile page (Markdown bio)
- Projects page (Markdown descriptions)
- Articles page (Markdown body)
- Uploaded assets (images/files) and external URLs

Public registration is disabled. Users are created via script.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Migrations

```bash
export FLASK_APP=run.py
python -m flask db init
python -m flask db migrate -m "initial"
python -m flask db upgrade
```

## Run

```bash
python run.py
```

Then open `http://127.0.0.1:5000`.

## Create a user

```bash
./scripts/create_user.sh <username> <email> <password>
```
