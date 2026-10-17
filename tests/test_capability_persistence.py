from datetime import UTC, datetime
from decimal import Decimal

from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

from crr.capability_model import Capability
from crr.models import Base, Organization


def test_capability_persists_exact_decimal_and_structured_fields() -> None:
    engine = create_engine("sqlite://")
    Base.metadata.create_all(engine)
    factory = sessionmaker(bind=engine, expire_on_commit=False)
    now = datetime(2026, 10, 18, 8, tzinfo=UTC)
    with factory.begin() as session:
        session.add(Organization(id="org_persist", name="Factory", status="ACTIVE", created_at=now))
        session.add(
            Capability(
                id="cap_persist",
                organization_id="org_persist",
                accepted_inputs=[{"state_type": "SCRAP"}],
                output_specifications={"state_type": "BILLET"},
                transformation_ids=["trn_1"],
                capacity_value=Decimal("123.450"),
                unit="t",
                unit_registry_version="CRR-UNITS-0.1",
                minimum_batch_value=Decimal("10.000"),
                location_id="loc_external",
                operating_window_start=now,
                operating_window_end=datetime(2026, 10, 18, 18, tzinfo=UTC),
                processing_cost={"currency": "SAR"},
                certifications=["CERT-A"],
                regulatory_constraints={"eligible": True},
                status="ACTIVE",
                version=1,
                created_by="act_external",
                provenance={"source_type": "TEST"},
                created_at=now,
                updated_at=now,
            )
        )
    with factory() as session:
        item = session.scalar(select(Capability).where(Capability.id == "cap_persist"))
        assert item is not None
        assert item.capacity_value == Decimal("123.450")
        assert item.minimum_batch_value == Decimal("10.000")
        assert item.accepted_inputs == [{"state_type": "SCRAP"}]
