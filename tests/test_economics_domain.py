from dataclasses import replace
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from crr.domain.economics import (
    EconomicComponent,
    EconomicComponentKind,
    EconomicModel,
    EconomicModelStatus,
    EconomicPerspective,
    Money,
    RoundingPolicy,
    evaluate_economic_model,
)
from crr.domain.errors import DomainError, TenantBoundaryError

NOW = datetime(2026, 10, 18, 12, tzinfo=UTC)


def make_model(
    *,
    status: EconomicModelStatus = EconomicModelStatus.ACTIVE,
    currency: str = "SAR",
) -> EconomicModel:
    return EconomicModel(
        id="eco_1",
        model_key="standard-route",
        organization_id="org_a",
        version=1,
        currency=currency,
        valid_from=datetime(2026, 10, 18, 0, tzinfo=UTC),
        valid_until=datetime(2026, 12, 31, tzinfo=UTC),
        calculation_version="1",
        rounding=RoundingPolicy("HALF_EVEN", 2),
        components=(
            EconomicComponent(
                EconomicPerspective.SUPPLIER,
                EconomicComponentKind.VALUE,
                "sale value",
                Money(Decimal("100.005"), currency),
                "contract",
            ),
            EconomicComponent(
                EconomicPerspective.SUPPLIER,
                EconomicComponentKind.COST,
                "transport",
                Money(Decimal("120.00"), currency),
                "tariff",
            ),
        ),
        status=status,
        created_by="act_a",
        provenance={"source_type": "TEST"},
        created_at=NOW,
        updated_at=NOW,
    )


def test_economic_evaluation_is_exact_and_preserves_negative_net():
    result = evaluate_economic_model(
        model=make_model(),
        organization_id="org_a",
        evaluated_at=NOW,
    )

    supplier = result.perspectives[0]
    assert supplier.value.amount == Decimal("100.00")
    assert supplier.cost.amount == Decimal("120.00")
    assert supplier.net.amount == Decimal("-20.00")


def test_economic_evaluation_is_deterministic():
    model = make_model()
    first = evaluate_economic_model(model=model, organization_id="org_a", evaluated_at=NOW)
    second = evaluate_economic_model(model=model, organization_id="org_a", evaluated_at=NOW)

    assert first == second


def test_cross_tenant_economic_model_is_blocked():
    with pytest.raises(TenantBoundaryError):
        evaluate_economic_model(model=make_model(), organization_id="org_b", evaluated_at=NOW)


def test_inactive_or_expired_model_cannot_be_evaluated():
    model = make_model(status=EconomicModelStatus.DRAFT)
    with pytest.raises(DomainError):
        evaluate_economic_model(model=model, organization_id="org_a", evaluated_at=NOW)


def test_mismatched_component_currency_is_blocked():
    wrong_currency = EconomicComponent(
        EconomicPerspective.SUPPLIER,
        EconomicComponentKind.VALUE,
        "wrong currency",
        Money(Decimal("1.00"), "USD"),
        "test",
    )
    with pytest.raises(DomainError):
        EconomicModel.__call__ if False else replace(make_model(), components=(wrong_currency,))


def test_negative_component_amount_is_blocked():
    with pytest.raises(DomainError):
        EconomicComponent(
            EconomicPerspective.SUPPLIER,
            EconomicComponentKind.COST,
            "invalid",
            Money(Decimal("-1.00"), "SAR"),
            "test",
        )
