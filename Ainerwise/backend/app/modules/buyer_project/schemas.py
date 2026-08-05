"""Buyer Project schemas."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    title: str
    project_type: str = "GENERAL"
    country: str | None = None
    city: str | None = None
    lat: float | None = None
    lng: float | None = None
    area_value: float | None = None
    area_unit: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    currency: str = "EUR"
    quality_preference: str = "NOT_SURE"
    description: str | None = None


class ProjectUpdate(BaseModel):
    title: str | None = None
    country: str | None = None
    city: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    quality_preference: str | None = None
    description: str | None = None


class ProjectRead(BaseModel):
    id: uuid.UUID
    buyer_id: uuid.UUID
    title: str
    project_type: str
    status: str
    country: str | None = None
    city: str | None = None
    budget_min: int | None = None
    budget_max: int | None = None
    currency: str = "EUR"
    quality_preference: str = "NOT_SURE"
    description: str | None = None
    ai_summary: str | None = None
    acceptance_criteria_json: list | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class LineItemRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    name: str
    description: str | None = None
    qty: float = 1
    unit: str = "pcs"
    quality_tier: str = "MID_RANGE"
    estimated_unit_price: float | None = None
    estimated_total_price: float | None = None
    currency: str = "EUR"
    confidence: float | None = None
    sourcing_notes: str | None = None
    category_hint: str | None = None
    source: str = "AI"
    status: str = "DRAFT"
    procurement_request_id: uuid.UUID | None = None
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class LineItemUpdate(BaseModel):
    name: str | None = None
    qty: float | None = None
    unit: str | None = None
    quality_tier: str | None = None
    status: str | None = None
    include_in_estimate: bool | None = None


class ProjectMessageCreate(BaseModel):
    content: str
    workflow_node: str | None = None


class ProjectMessageRead(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    role: str
    workflow_node: str | None = None
    content: str
    created_at: datetime | None = None

    model_config = {"from_attributes": True}


class ProjectMetricPatch(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    label: str | None = Field(default=None, max_length=200)
    value: Any
    source: str = "USER"
    confidence: float | None = Field(default=None, ge=0, le=1)


class ProjectMetricsUpdate(BaseModel):
    metrics: list[ProjectMetricPatch] = Field(min_length=1, max_length=100)


class ProjectReportRowPatch(BaseModel):
    selected_tier: str | None = None
    include_in_total: bool | None = None
    selected_for_purchase: bool | None = None
    notes: str | None = None
