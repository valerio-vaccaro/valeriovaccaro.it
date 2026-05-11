#!/usr/bin/env bash
set -euo pipefail

if [ $# -lt 3 ]; then
  echo "Usage: $0 <username> <email> <password>"
  exit 1
fi

USERNAME="$1"
EMAIL="$2"
PASSWORD="$3"

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if [ ! -d ".venv" ]; then
  echo "Missing .venv. Create it first: python3 -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt"
  exit 1
fi

source .venv/bin/activate

python - "$USERNAME" "$EMAIL" "$PASSWORD" << 'PY'
import sys
from app import create_app, db
from app.models import User, Profile

username = sys.argv[1].strip()
email = sys.argv[2].strip().lower()
password = sys.argv[3]

if len(password) < 8:
    print("Error: password must be at least 8 chars")
    raise SystemExit(1)

app = create_app()
with app.app_context():
    exists = User.query.filter((User.username == username) | (User.email == email)).first()
    if exists:
        print("Error: user/email already exists")
        raise SystemExit(1)

    user = User(username=username, email=email)
    user.set_password(password)
    db.session.add(user)
    db.session.flush()

    profile = Profile(user_id=user.id, title=f"{username}'s site", markdown_bio="## About me\nWrite here.")
    db.session.add(profile)
    db.session.commit()

    print(f"Created user: {username} ({email})")
PY
