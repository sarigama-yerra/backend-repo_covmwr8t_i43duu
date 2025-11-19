import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from bson import ObjectId

from database import db, create_document, get_documents
from schemas import Vendor, Contact, Deal, Note

app = FastAPI(title="Vendor CRM API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Utilities
class MongoJSONEncoder(BaseModel):
    model_config = {
        "json_encoders": {ObjectId: str}
    }


def to_object_id(id_str: str) -> ObjectId:
    try:
        return ObjectId(id_str)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid id format")


def serialize(doc: Dict[str, Any]):
    if not doc:
        return doc
    doc["id"] = str(doc.pop("_id"))
    return doc


@app.get("/")
def read_root():
    return {"message": "Vendor CRM API running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": None,
        "database_name": None,
        "connection_status": "Not Connected",
        "collections": []
    }

    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["database_url"] = "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set"
            response["database_name"] = db.name if hasattr(db, 'name') else "✅ Connected"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:50]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:50]}"

    return response


# Onboarding: create a vendor profile
@app.post("/vendors", response_model=dict)
async def create_vendor(vendor: Vendor):
    vendor_id = create_document("vendor", vendor)
    return {"id": vendor_id}


# Vendor listing with optional search by business_name
@app.get("/vendors", response_model=List[dict])
async def list_vendors(q: Optional[str] = None, limit: int = 50):
    filt: Dict[str, Any] = {}
    if q:
        # Basic case-insensitive contains search on business_name
        filt = {"business_name": {"$regex": q, "$options": "i"}}
    docs = get_documents("vendor", filt, limit)
    return [serialize(d) for d in docs]


# Business management: contacts
@app.post("/contacts", response_model=dict)
async def create_contact(contact: Contact):
    # Validate vendor exists
    v = db["vendor"].find_one({"_id": to_object_id(contact.vendor_id)})
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    contact_id = create_document("contact", contact)
    return {"id": contact_id}


@app.get("/contacts", response_model=List[dict])
async def list_contacts(vendor_id: Optional[str] = None, limit: int = 100):
    filt: Dict[str, Any] = {}
    if vendor_id:
        filt["vendor_id"] = vendor_id
    docs = get_documents("contact", filt, limit)
    return [serialize(d) for d in docs]


# Deals / pipeline
@app.post("/deals", response_model=dict)
async def create_deal(deal: Deal):
    v = db["vendor"].find_one({"_id": to_object_id(deal.vendor_id)})
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    deal_id = create_document("deal", deal)
    return {"id": deal_id}


@app.get("/deals", response_model=List[dict])
async def list_deals(vendor_id: Optional[str] = None, stage: Optional[str] = None, limit: int = 100):
    filt: Dict[str, Any] = {}
    if vendor_id:
        filt["vendor_id"] = vendor_id
    if stage:
        filt["stage"] = stage
    docs = get_documents("deal", filt, limit)
    return [serialize(d) for d in docs]


# Notes on vendor
@app.post("/notes", response_model=dict)
async def create_note(note: Note):
    v = db["vendor"].find_one({"_id": to_object_id(note.vendor_id)})
    if not v:
        raise HTTPException(status_code=404, detail="Vendor not found")
    note_id = create_document("note", note)
    return {"id": note_id}


@app.get("/notes", response_model=List[dict])
async def list_notes(vendor_id: str, limit: int = 100):
    docs = get_documents("note", {"vendor_id": vendor_id}, limit)
    return [serialize(d) for d in docs]


# Simple schema endpoint to aid admin tools
@app.get("/schema", response_model=Dict[str, Any])
async def get_schema():
    return {
        "vendor": Vendor.model_json_schema(),
        "contact": Contact.model_json_schema(),
        "deal": Deal.model_json_schema(),
        "note": Note.model_json_schema(),
    }


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
