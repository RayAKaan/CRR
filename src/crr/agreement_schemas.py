"""Request schemas for the Agreement API."""

from pydantic import BaseModel, ConfigDict, Field


class AgreementCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    offer_id: str = Field(min_length=1, max_length=80)


class AgreementLifecycleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(CANCELLED|TERMINATED)$")
