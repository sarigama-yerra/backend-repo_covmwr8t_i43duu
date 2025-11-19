"""
Database Schemas for Vendor CRM

Each Pydantic model represents a MongoDB collection. The collection name
is the lowercase class name. These schemas are returned by GET /schema for
introspection and are used for validation in API routes.
"""

from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Literal

class Vendor(BaseModel):
    name: str = Field(..., description="Primary contact full name")
    email: EmailStr = Field(..., description="Primary contact email")
    business_name: str = Field(..., description="Registered business name")
    phone: Optional[str] = Field(None, description="Primary phone number")
    category: Optional[str] = Field(None, description="Business category or industry")
    website: Optional[str] = Field(None, description="Business website URL")
    status: Literal["active", "pending", "suspended"] = Field(
        "active", description="Vendor account status"
    )

class Contact(BaseModel):
    vendor_id: str = Field(..., description="Associated vendor id (string)")
    name: str = Field(..., description="Contact full name")
    email: Optional[EmailStr] = Field(None, description="Contact email")
    phone: Optional[str] = Field(None, description="Contact phone number")
    role: Optional[str] = Field(None, description="Role or title")

class Deal(BaseModel):
    vendor_id: str = Field(..., description="Associated vendor id (string)")
    title: str = Field(..., description="Deal title or summary")
    value: float = Field(..., ge=0, description="Estimated deal value")
    stage: Literal[
        "lead",
        "qualified",
        "proposal",
        "won",
        "lost",
    ] = Field("lead", description="Current pipeline stage")
    notes: Optional[str] = Field(None, description="Additional notes")

class Note(BaseModel):
    vendor_id: str = Field(..., description="Associated vendor id (string)")
    content: str = Field(..., description="Note content")
    author: Optional[str] = Field(None, description="Author name or id")
