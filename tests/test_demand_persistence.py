from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

import crr.demand_model  # noqa: F401
from crr.models import Base, Demand


def test_demand_table_round_trips_exact_quantities_and_metadata():
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    now = datetime(2026, 10, 18, tzinfo=UTC)
    with Session(engine) as session:
        # Reference integrity is covered by the migration/API conformance suite; this test
        # isolates exact persistence behavior after the model is registered.
        from crr.models import Actor, Organization

        session.add(Organization(id="org_d", name="Demand Org", status="ACTIVE", created_at=now))
        session.add(
            Actor(
                id="act_d",
                organization_id="org_d",
                name="Demand Admin",
                role="ORG_ADMIN",
                active=True,
                created_at=now,
            )
        )
        session.flush()
        session.add(
            Demand(
                id="dem_d",
                organization_id="org_d",
                required_state="ALUMINUM_SCRAP",
                quantity_min_value=Decimal("0.000"),
                quantity_target_value=Decimal("20.000"),
                quantity_max_value=Decimal("30.000"),
                remaining_quantity_value=Decimal("20.000"),
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                status="DRAFT",
                location_constraints={},
                timing_start=now,
                timing_end=datetime(2026, 10, 20, tzinfo=UTC),
                quality_requirements={},
                pricing_constraints={},
                certifications=[],
                regulatory_constraints={},
                substitutions=[],
                recurrence={},
                version=1,
                created_by="act_d",
                provenance={"source_type": "TEST"},
                created_at=now,
                updated_at=now,
            )
        )
        session.commit()
        demand = session.scalar(select(Demand).where(Demand.id == "dem_d"))
        assert demand is not None
        assert demand.quantity_target_value == Decimal("20.000")
        assert demand.remaining_quantity_value == Decimal("20.000")
        assert demand.organization_id == "org_d"
