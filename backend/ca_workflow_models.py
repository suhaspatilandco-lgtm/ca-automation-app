from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
import uuid

# Business Type Enum
class BusinessType(str, Enum):
    PROPRIETORSHIP = "PROPRIETORSHIP"
    PARTNERSHIP = "PARTNERSHIP"
    LLP = "LLP"
    PRIVATE_LIMITED = "PRIVATE_LIMITED"
    PUBLIC_LIMITED = "PUBLIC_LIMITED"
    TRUST = "TRUST"
    HUF = "HUF"
    INDIVIDUAL = "INDIVIDUAL"

# Work-in-Progress Stage
class WIPStage(str, Enum):
    DATA_COLLECTION = "DATA_COLLECTION"
    UNDER_PREPARATION = "UNDER_PREPARATION"
    REVIEW = "REVIEW"
    CLIENT_APPROVAL = "CLIENT_APPROVAL"
    FILING = "FILING"
    ACKNOWLEDGMENT_RECEIVED = "ACKNOWLEDGMENT_RECEIVED"
    COMPLETED = "COMPLETED"

# Query Status
class QueryStatus(str, Enum):
    OPEN = "OPEN"
    PENDING_CLIENT = "PENDING_CLIENT"
    RESOLVED = "RESOLVED"
    CLOSED = "CLOSED"

# Enhanced Client Model with Business Type
class ClientExtended(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    business_type: BusinessType
    gstin: Optional[str] = None
    pan: Optional[str] = None
    tan: Optional[str] = None  # For TDS
    cin: Optional[str] = None  # Corporate Identity Number
    turnover: Optional[float] = None  # Annual turnover
    
    # Multiple GSTINs for multi-state operations
    additional_gstins: Optional[List[Dict[str, str]]] = []  # [{"state": "Maharashtra", "gstin": "27XXX"}]
    
    # Other registrations
    iec_code: Optional[str] = None  # Import Export Code
    fssai_license: Optional[str] = None
    
    # Compliance requirements based on business type
    requires_audit: bool = False
    requires_gst: bool = True
    requires_tds: bool = False
    requires_roc_filing: bool = False
    
    address: Optional[str] = None
    status: str = "ACTIVE"
    created_at: datetime = Field(default_factory=datetime.now)

# Financial Year Model
class FinancialYear(BaseModel):
    fy_code: str  # "FY2024-25"
    start_date: datetime  # 2024-04-01
    end_date: datetime  # 2025-03-31
    ay_code: str  # "AY2025-26" (Assessment Year)
    current: bool = False

# Enhanced Task with WIP Stage
class TaskExtended(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    client_id: str
    client_name: Optional[str] = None
    task_type: str
    
    # WIP Stage tracking
    wip_stage: WIPStage = WIPStage.DATA_COLLECTION
    
    # Financial Year tracking
    financial_year: Optional[str] = None  # "FY2024-25"
    quarter: Optional[int] = None  # 1, 2, 3, 4
    
    due_date: datetime
    status: str = "PENDING"
    priority: str = "MEDIUM"
    assigned_to: Optional[str] = None
    
    # Acknowledgment details
    acknowledgment_number: Optional[str] = None  # ARN after filing
    filing_date: Optional[datetime] = None
    challan_details: Optional[Dict[str, Any]] = None
    
    # Checklist for this task
    checklist: Optional[List[Dict[str, Any]]] = []  # [{"item": "Form 16 received", "completed": false}]
    
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)

# Query Model
class Query(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    task_id: str
    client_id: str
    client_name: Optional[str] = None
    
    query_text: str
    raised_by: str  # Staff member name
    raised_at: datetime = Field(default_factory=datetime.now)
    
    status: QueryStatus = QueryStatus.OPEN
    
    # Client response
    response: Optional[str] = None
    responded_at: Optional[datetime] = None
    
    # Query aging
    days_pending: int = 0
    
    # Follow-up reminders sent
    reminders_sent: int = 0
    last_reminder_at: Optional[datetime] = None

class QueryCreate(BaseModel):
    task_id: str
    client_id: str
    query_text: str
    raised_by: str

class QueryResponse(BaseModel):
    query_id: str
    response: str

# Checklist Item
class ChecklistItem(BaseModel):
    item: str
    completed: bool = False
    completed_at: Optional[datetime] = None
    notes: Optional[str] = None

# Compliance Requirement based on Business Type
COMPLIANCE_MATRIX = {
    BusinessType.PROPRIETORSHIP: {
        "requires_gst": "conditional",  # If turnover > 40L
        "requires_audit": "conditional",  # If turnover > 1Cr
        "requires_tds": False,
        "requires_roc_filing": False,
        "applicable_returns": ["ITR", "GST"]
    },
    BusinessType.PARTNERSHIP: {
        "requires_gst": "conditional",
        "requires_audit": True,
        "requires_tds": "conditional",
        "requires_roc_filing": False,
        "applicable_returns": ["ITR", "GST", "TDS"]
    },
    BusinessType.LLP: {
        "requires_gst": "conditional",
        "requires_audit": True,
        "requires_tds": True,
        "requires_roc_filing": True,
        "applicable_returns": ["ITR", "GST", "TDS", "ROC", "AUDIT"]
    },
    BusinessType.PRIVATE_LIMITED: {
        "requires_gst": "conditional",
        "requires_audit": True,
        "requires_tds": True,
        "requires_roc_filing": True,
        "applicable_returns": ["ITR", "GST", "TDS", "ROC", "AUDIT"]
    },
    BusinessType.PUBLIC_LIMITED: {
        "requires_gst": True,
        "requires_audit": True,
        "requires_tds": True,
        "requires_roc_filing": True,
        "applicable_returns": ["ITR", "GST", "TDS", "ROC", "AUDIT"]
    },
    BusinessType.TRUST: {
        "requires_gst": "conditional",
        "requires_audit": "conditional",
        "requires_tds": True,
        "requires_roc_filing": False,
        "applicable_returns": ["ITR", "GST", "TDS"]
    },
    BusinessType.HUF: {
        "requires_gst": "conditional",
        "requires_audit": "conditional",
        "requires_tds": False,
        "requires_roc_filing": False,
        "applicable_returns": ["ITR", "GST"]
    },
    BusinessType.INDIVIDUAL: {
        "requires_gst": False,
        "requires_audit": False,
        "requires_tds": False,
        "requires_roc_filing": False,
        "applicable_returns": ["ITR"]
    }
}

# Service-specific detailed checklists
SERVICE_CHECKLISTS = {
    "ITR_INDIVIDUAL": [
        {"item": "Form 16 received from employer", "mandatory": True},
        {"item": "Form 26AS downloaded and verified", "mandatory": True},
        {"item": "Bank statements for all accounts", "mandatory": True},
        {"item": "Interest certificates from banks", "mandatory": False},
        {"item": "House property details (rent, loan interest)", "mandatory": False},
        {"item": "Capital gains computation", "mandatory": False},
        {"item": "Investment proofs (80C, 80D, 80G)", "mandatory": False},
        {"item": "Other income details (dividend, interest)", "mandatory": False},
        {"item": "Previous year refund received confirmation", "mandatory": False},
    ],
    "ITR_BUSINESS": [
        {"item": "Books of accounts finalized", "mandatory": True},
        {"item": "Trial balance prepared", "mandatory": True},
        {"item": "Profit & Loss account", "mandatory": True},
        {"item": "Balance sheet", "mandatory": True},
        {"item": "Tax audit report (if applicable)", "mandatory": "conditional"},
        {"item": "Advance tax payment challans", "mandatory": False},
        {"item": "TDS certificates", "mandatory": False},
        {"item": "Depreciation schedule", "mandatory": True},
    ],
    "GST_MONTHLY": [
        {"item": "Sales register finalized", "mandatory": True},
        {"item": "Purchase register finalized", "mandatory": True},
        {"item": "GSTR-2A downloaded and reconciled", "mandatory": True},
        {"item": "E-way bills accounted for", "mandatory": False},
        {"item": "Credit notes issued", "mandatory": False},
        {"item": "Debit notes received", "mandatory": False},
        {"item": "Exports documentation", "mandatory": False},
        {"item": "HSN codes verified", "mandatory": True},
    ],
    "TDS_QUARTERLY": [
        {"item": "TDS challan details collected", "mandatory": True},
        {"item": "Deductee details (PAN, amount) prepared", "mandatory": True},
        {"item": "Form 15G/15H collected (if applicable)", "mandatory": False},
        {"item": "Late payment interest calculated", "mandatory": False},
        {"item": "FVU file prepared", "mandatory": True},
    ],
    "AUDIT": [
        {"item": "All vouchers collected", "mandatory": True},
        {"item": "Bank statements for full year", "mandatory": True},
        {"item": "Stock register", "mandatory": True},
        {"item": "Fixed assets register", "mandatory": True},
        {"item": "Loan agreements", "mandatory": False},
        {"item": "Board resolutions", "mandatory": "conditional"},
        {"item": "Related party transactions details", "mandatory": False},
    ],
    "ROC_ANNUAL": [
        {"item": "Board meeting for accounts approval", "mandatory": True},
        {"item": "AGM notice sent to members", "mandatory": True},
        {"item": "AGM conducted", "mandatory": True},
        {"item": "Financial statements finalized", "mandatory": True},
        {"item": "AOC-4 form prepared", "mandatory": True},
        {"item": "MGT-7 form prepared", "mandatory": True},
        {"item": "Digital signature certificates ready", "mandatory": True},
    ]
}
