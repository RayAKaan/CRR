"""Create the first tenant administrator and a hashed bearer API key."""

from __future__ import annotations

import argparse
import hashlib
import secrets
from datetime import UTC, datetime

from alembic import command
from alembic.config import Config

from crr.database import SessionLocal
from crr.models import Actor, APIKey, Organization


def bootstrap(organization_id: str, organization_name: str, actor_id: str, actor_name: str) -> str:
    command.upgrade(Config("alembic.ini"), "head")
    token = "crr_" + secrets.token_urlsafe(32)
    now = datetime.now(UTC)
    with SessionLocal.begin() as session:
        if session.get(Organization, organization_id) is not None:
            raise ValueError("Organization already exists.")
        session.add(
            Organization(
                id=organization_id,
                name=organization_name,
                status="ACTIVE",
                created_at=now,
            )
        )
        session.add(
            Actor(
                id=actor_id,
                organization_id=organization_id,
                name=actor_name,
                role="ORG_ADMIN",
                active=True,
                created_at=now,
            )
        )
        session.add(
            APIKey(
                id="key_" + secrets.token_hex(12),
                organization_id=organization_id,
                actor_id=actor_id,
                secret_hash=hashlib.sha256(token.encode("utf-8")).hexdigest(),
                scopes=["admin:*"],
                revoked=False,
                created_at=now,
            )
        )
    return token


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--organization-id", required=True)
    parser.add_argument("--organization-name", required=True)
    parser.add_argument("--actor-id", required=True)
    parser.add_argument("--actor-name", required=True)
    args = parser.parse_args()
    print(bootstrap(args.organization_id, args.organization_name, args.actor_id, args.actor_name))


if __name__ == "__main__":
    main()
