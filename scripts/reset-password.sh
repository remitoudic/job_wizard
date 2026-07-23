#!/usr/bin/env bash
# Reset password script for Job Wizard user

set -euo pipefail

EMAIL="${1:-remitoudic@gmail.com}"
PASSWORD="${2:-remitoudic}"

echo "🔐 Resetting password for $EMAIL..."

BACKEND_CONTAINER=$(docker ps -q -f name=jobwizard_backend | head -n 1)

if [ -z "$BACKEND_CONTAINER" ]; then
    BACKEND_CONTAINER=$(docker ps -q -f name=jobwizard-backend | head -n 1)
fi

if [ -z "$BACKEND_CONTAINER" ]; then
    echo "❌ Error: Backend container is not running!"
    exit 1
fi

docker exec "$BACKEND_CONTAINER" python -c "
from sqlmodel import Session, select
from database_pkg import engine
from database_pkg.models.user import User
from app.core.security import get_password_hash

with Session(engine) as session:
    user = session.exec(select(User).where(User.email == '$EMAIL')).first()
    if user:
        user.hashed_password = get_password_hash('$PASSWORD')
        session.add(user)
        session.commit()
        print('✅ Password successfully updated for $EMAIL')
    else:
        print('❌ User $EMAIL not found')
"
