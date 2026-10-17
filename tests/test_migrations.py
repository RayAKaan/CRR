from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.orm import Session

from crr.models import Actor, Location, Organization, Resource, ResourceState


def test_initial_migration_builds_schema_and_protects_physical_history(tmp_path: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    database_path = tmp_path / "phase1.db"
    config = Config(str(root / "alembic.ini"))
    config.set_main_option("script_location", str(root / "migrations"))
    config.set_main_option("sqlalchemy.url", f"sqlite:///{database_path.as_posix()}")
    command.upgrade(config, "head")
    command.check(config)

    engine = create_engine(f"sqlite:///{database_path.as_posix()}")
    with engine.connect() as connection:
        tables = set(
            connection.execute(text("SELECT name FROM sqlite_master WHERE type='table'")).scalars()
        )
        assert {
            "organizations",
            "actors",
            "resources",
            "resource_states",
            "state_transitions",
            "outbox_events",
        } <= tables
        triggers = set(
            connection.execute(
                text("SELECT name FROM sqlite_master WHERE type='trigger'")
            ).scalars()
        )
        assert {
            "resource_states_no_update",
            "resource_states_no_delete",
            "state_transitions_no_update",
            "state_transitions_no_delete",
            "outbox_events_no_update",
            "outbox_events_no_delete",
        } <= triggers

    now = datetime.now(UTC)
    with Session(engine) as session, session.begin():
        session.add(Organization(id="org_1", name="Factory", status="ACTIVE", created_at=now))
        session.flush()
        session.add(
            Actor(
                id="act_1",
                organization_id="org_1",
                name="Operator",
                role="OPERATOR",
                active=True,
                created_at=now,
            )
        )
        session.add(
            Location(
                id="loc_1", organization_id="org_1", name="Yard", provenance={}, created_at=now
            )
        )
        session.add(
            Resource(
                id="res_1",
                organization_id="org_1",
                resource_type="ALUMINUM",
                version=1,
                created_by="act_1",
                provenance={},
                created_at=now,
            )
        )
        session.flush()
        session.add(
            ResourceState(
                id="rst_1",
                organization_id="org_1",
                resource_id="res_1",
                resource_version=1,
                state_type="SCRAP",
                quantity_value=Decimal("1.0"),
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                location_id="loc_1",
                effective_at=now,
                recorded_at=now,
                created_by="act_1",
                provenance={},
                quality={},
                physical_properties={},
                predecessor_state_ids=[],
            )
        )

    with pytest.raises(DBAPIError, match="immutable"):
        with engine.begin() as connection:
            connection.execute(
                text("UPDATE resource_states SET state_type='FORGED' WHERE id='rst_1'")
            )
