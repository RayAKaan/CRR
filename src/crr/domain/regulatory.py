"""Deterministic regulatory, safety, and eligibility checks for routing."""

from __future__ import annotations

from typing import Any

from crr.domain.capability import Capability
from crr.domain.demand import Demand
from crr.domain.errors import DomainError, TenantBoundaryError
from crr.domain.routing import Rejection
from crr.domain.transformation import Transformation


def _reject(code: str, object_id: str, message: str) -> Rejection:
    return Rejection(code=code, object_id=object_id, message=message)


def _list_values(value: Any, field: str, object_id: str) -> tuple[str, ...]:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(item, str) and item for item in value):
        raise DomainError(f"{field} on {object_id} must be a list of non-empty strings.")
    return tuple(value)


def _mapping(value: Any, field: str, object_id: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise DomainError(f"{field} on {object_id} must be an object.")
    return value


def _required_controls(source: dict[str, Any]) -> dict[str, Any]:
    controls = source.get("required_controls", {})
    if controls is None:
        return {}
    if not isinstance(controls, dict):
        raise DomainError("required_controls must be an object.")
    return controls


def _prohibited_controls(source: dict[str, Any]) -> dict[str, Any]:
    controls = source.get("prohibited_controls", {})
    if controls is None:
        return {}
    if not isinstance(controls, dict):
        raise DomainError("prohibited_controls must be an object.")
    return controls


def _uncertain(source: dict[str, Any]) -> bool:
    return bool(source.get("regulatory_uncertainty") or source.get("uncertain"))


def evaluate_regulatory_eligibility(
    *,
    demand: Demand,
    capability: Capability,
    transformation: Transformation,
) -> tuple[Rejection, ...]:
    """Evaluate only explicitly represented regulatory/safety facts.

    This function never interprets law or infers permission. Missing mandatory
    controls are hard blockers; uncertainty is also a blocker so callers cannot
    accidentally treat unresolved policy as authorization.
    """
    organization_id = demand.organization_id
    if capability.organization_id != organization_id:
        raise TenantBoundaryError("Capability belongs to another organization.")
    if transformation.organization_id != organization_id:
        raise TenantBoundaryError("Transformation belongs to another organization.")

    capability_controls = _mapping(
        capability.regulatory_constraints, "regulatory_constraints", capability.id
    )
    demand_controls = _mapping(
        demand.regulatory_constraints, "regulatory_constraints", demand.id
    )
    transformation_controls = _mapping(
        transformation.regulatory_requirements, "regulatory_requirements", transformation.id
    )

    rejections: list[Rejection] = []

    required_certifications = set(
        _list_values(
            transformation_controls.get("required_certifications"),
            "required_certifications",
            transformation.id,
        )
    )
    required_certifications.update(
        _list_values(
            demand_controls.get("required_certifications"),
            "required_certifications",
            demand.id,
        )
    )
    missing_certifications = sorted(required_certifications - set(capability.certifications))
    if missing_certifications:
        rejections.append(
            _reject(
                "REGULATORY_BLOCK",
                capability.id,
                "Required certification(s) are missing: " + ", ".join(missing_certifications),
            )
        )

    required_controls: dict[str, Any] = {}
    for source in (transformation_controls, demand_controls):
        for key, expected in _required_controls(source).items():
            if key in required_controls and required_controls[key] != expected:
                rejections.append(
                    _reject(
                        "REGULATORY_BLOCK",
                        transformation.id,
                        f"Conflicting required regulatory control: {key}.",
                    )
                )
            required_controls[key] = expected

    for key, expected in required_controls.items():
        if capability_controls.get(key) != expected:
            rejections.append(
                _reject(
                    "REGULATORY_BLOCK",
                    capability.id,
                    f"Required regulatory control {key!r} is not satisfied.",
                )
            )

    prohibited: dict[str, Any] = {}
    for source in (transformation_controls, demand_controls):
        prohibited.update(_prohibited_controls(source))
    for key, forbidden in prohibited.items():
        if capability_controls.get(key) == forbidden:
            rejections.append(
                _reject(
                    "SAFETY_BLOCK" if "safety" in key.lower() else "REGULATORY_BLOCK",
                    capability.id,
                    f"Prohibited regulatory control {key!r} is present.",
                )
            )

    if _uncertain(transformation_controls) or _uncertain(demand_controls):
        rejections.append(
            _reject(
                "REGULATORY_BLOCK",
                transformation.id,
                "Mandatory regulatory eligibility is unresolved; human/policy review is required.",
            )
        )

    safety_controls = transformation_controls.get("required_safety_controls", [])
    safety_controls += demand_controls.get("required_safety_controls", []) if isinstance(
        demand_controls.get("required_safety_controls", []), list
    ) else []
    required_safety = _list_values(safety_controls, "required_safety_controls", transformation.id)
    for control in required_safety:
        if capability_controls.get("safety_controls", {}).get(control) is not True:
            rejections.append(
                _reject(
                    "SAFETY_BLOCK",
                    capability.id,
                    f"Required safety control {control!r} is not satisfied.",
                )
            )

    return tuple(rejections)
