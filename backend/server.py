from fastapi import FastAPI, APIRouter, HTTPException, Depends, UploadFile, File, Response
from fastapi.responses import FileResponse, StreamingResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional
import uuid
from datetime import datetime, timezone
from enum import Enum

# Import production services
from auth import get_current_user, User
from auth_routes import router as auth_router
from email_service import email_service
from file_service import file_service
from pdf_service import pdf_service
from automation_service import automation_service
from bulk_import_service import bulk_import_service
from document_intelligence import document_intelligence
from template_service import template_service

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="CA Practice Automation API", version="2.0.0")

# Mount uploads directory for file serving
uploads_dir = Path("/app/backend/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Enums
class TaskType(str, Enum):
    GST = "GST"
    ITR = "ITR"
    AUDIT = "AUDIT"
    ROC = "ROC"
    GENERAL = "GENERAL"

class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    OVERDUE = "OVERDUE"

class Priority(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    URGENT = "URGENT"

class InvoiceStatus(str, Enum):
    DRAFT = "DRAFT"
    SENT = "SENT"
    PAID = "PAID"
    OVERDUE = "OVERDUE"

class ClientStatus(str, Enum):
    ACTIVE = "ACTIVE"
    INACTIVE = "INACTIVE"

# Models
class Client(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    phone: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    status: ClientStatus = ClientStatus.ACTIVE
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class ClientCreate(BaseModel):
    name: str
    email: str
    phone: str
    gstin: Optional[str] = None
    pan: Optional[str] = None
    address: Optional[str] = None
    status: Optional[ClientStatus] = ClientStatus.ACTIVE

class Task(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: Optional[str] = None
    client_id: str
    client_name: Optional[str] = None
    task_type: TaskType
    due_date: datetime
    status: TaskStatus = TaskStatus.PENDING
    priority: Priority = Priority.MEDIUM
    assigned_to: Optional[str] = None
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class TaskCreate(BaseModel):
    title: str
    description: Optional[str] = None
    client_id: str
    task_type: TaskType
    due_date: datetime
    status: Optional[TaskStatus] = TaskStatus.PENDING
    priority: Optional[Priority] = Priority.MEDIUM
    assigned_to: Optional[str] = None

class Document(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    client_name: Optional[str] = None
    filename: str
    file_url: str
    category: str
    uploaded_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class DocumentCreate(BaseModel):
    client_id: str
    filename: str
    file_url: str
    category: str

class InvoiceItem(BaseModel):
    description: str
    quantity: int
    rate: float
    amount: float

class Invoice(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_id: str
    client_name: Optional[str] = None
    invoice_number: str
    items: List[InvoiceItem]
    subtotal: float
    tax: float
    total: float
    status: InvoiceStatus = InvoiceStatus.DRAFT
    due_date: datetime
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class InvoiceCreate(BaseModel):
    client_id: str
    invoice_number: str
    items: List[InvoiceItem]
    subtotal: float
    tax: float
    total: float
    status: Optional[InvoiceStatus] = InvoiceStatus.DRAFT
    due_date: datetime

class Staff(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    email: str
    role: str
    phone: str
    joined_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StaffCreate(BaseModel):
    name: str
    email: str
    role: str
    phone: str

class DashboardStats(BaseModel):
    total_clients: int
    active_tasks: int
    pending_invoices: int
    total_revenue: float
    upcoming_deadlines: List[Task]

# Helper function to serialize datetime
def serialize_datetime(obj):
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj

# Routes
@api_router.get("/")
async def root():
    return {"message": "CA Practice Automation API"}

# Client Routes
@api_router.post("/clients", response_model=Client)
async def create_client(client_input: ClientCreate):
    client_dict = client_input.model_dump()
    client = Client(**client_dict)
    doc = client.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    await db.clients.insert_one(doc)
    return client

@api_router.get("/clients", response_model=List[Client])
async def get_clients(status: Optional[str] = None):
    query = {}
    if status:
        query['status'] = status
    clients = await db.clients.find(query, {"_id": 0}).to_list(1000)
    for client in clients:
        if isinstance(client.get('created_at'), str):
            client['created_at'] = datetime.fromisoformat(client['created_at'])
    return clients

@api_router.get("/clients/{client_id}", response_model=Client)
async def get_client(client_id: str):
    client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if not client:
        raise HTTPException(status_code=404, detail="Client not found")
    if isinstance(client.get('created_at'), str):
        client['created_at'] = datetime.fromisoformat(client['created_at'])
    return client

@api_router.put("/clients/{client_id}", response_model=Client)
async def update_client(client_id: str, client_input: ClientCreate):
    client_dict = client_input.model_dump()
    result = await db.clients.update_one({"id": client_id}, {"$set": client_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    updated_client = await db.clients.find_one({"id": client_id}, {"_id": 0})
    if isinstance(updated_client.get('created_at'), str):
        updated_client['created_at'] = datetime.fromisoformat(updated_client['created_at'])
    return updated_client

@api_router.delete("/clients/{client_id}")
async def delete_client(client_id: str):
    result = await db.clients.delete_one({"id": client_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Client not found")
    return {"message": "Client deleted successfully"}

# Task Routes
@api_router.post("/tasks", response_model=Task)
async def create_task(task_input: TaskCreate):
    task_dict = task_input.model_dump()
    # Get client name
    client = await db.clients.find_one({"id": task_dict['client_id']}, {"_id": 0})
    if client:
        task_dict['client_name'] = client['name']
    task = Task(**task_dict)
    doc = task.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['due_date'] = doc['due_date'].isoformat()
    await db.tasks.insert_one(doc)
    return task

@api_router.get("/tasks", response_model=List[Task])
async def get_tasks(status: Optional[str] = None, task_type: Optional[str] = None):
    query = {}
    if status:
        query['status'] = status
    if task_type:
        query['task_type'] = task_type
    tasks = await db.tasks.find(query, {"_id": 0}).to_list(1000)
    for task in tasks:
        if isinstance(task.get('created_at'), str):
            task['created_at'] = datetime.fromisoformat(task['created_at'])
        if isinstance(task.get('due_date'), str):
            task['due_date'] = datetime.fromisoformat(task['due_date'])
    return tasks

@api_router.get("/tasks/{task_id}", response_model=Task)
async def get_task(task_id: str):
    task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    if isinstance(task.get('created_at'), str):
        task['created_at'] = datetime.fromisoformat(task['created_at'])
    if isinstance(task.get('due_date'), str):
        task['due_date'] = datetime.fromisoformat(task['due_date'])
    return task

@api_router.put("/tasks/{task_id}", response_model=Task)
async def update_task(task_id: str, task_input: TaskCreate):
    task_dict = task_input.model_dump()
    # Get client name
    client = await db.clients.find_one({"id": task_dict['client_id']}, {"_id": 0})
    if client:
        task_dict['client_name'] = client['name']
    task_dict['due_date'] = task_dict['due_date'].isoformat()
    result = await db.tasks.update_one({"id": task_id}, {"$set": task_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    updated_task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
    if isinstance(updated_task.get('created_at'), str):
        updated_task['created_at'] = datetime.fromisoformat(updated_task['created_at'])
    if isinstance(updated_task.get('due_date'), str):
        updated_task['due_date'] = datetime.fromisoformat(updated_task['due_date'])
    return updated_task

@api_router.delete("/tasks/{task_id}")
async def delete_task(task_id: str):
    result = await db.tasks.delete_one({"id": task_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"message": "Task deleted successfully"}

# Document Routes
@api_router.post("/documents", response_model=Document)
async def create_document(doc_input: DocumentCreate):
    doc_dict = doc_input.model_dump()
    # Get client name
    client = await db.clients.find_one({"id": doc_dict['client_id']}, {"_id": 0})
    if client:
        doc_dict['client_name'] = client['name']
    document = Document(**doc_dict)
    doc = document.model_dump()
    doc['uploaded_at'] = doc['uploaded_at'].isoformat()
    await db.documents.insert_one(doc)
    return document

@api_router.get("/documents", response_model=List[Document])
async def get_documents(client_id: Optional[str] = None):
    query = {}
    if client_id:
        query['client_id'] = client_id
    documents = await db.documents.find(query, {"_id": 0}).to_list(1000)
    for doc in documents:
        if isinstance(doc.get('uploaded_at'), str):
            doc['uploaded_at'] = datetime.fromisoformat(doc['uploaded_at'])
    return documents

@api_router.delete("/documents/{doc_id}")
async def delete_document(doc_id: str):
    result = await db.documents.delete_one({"id": doc_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"message": "Document deleted successfully"}

# Invoice Routes
@api_router.post("/invoices", response_model=Invoice)
async def create_invoice(invoice_input: InvoiceCreate):
    invoice_dict = invoice_input.model_dump()
    # Get client name
    client = await db.clients.find_one({"id": invoice_dict['client_id']}, {"_id": 0})
    if client:
        invoice_dict['client_name'] = client['name']
    invoice = Invoice(**invoice_dict)
    doc = invoice.model_dump()
    doc['created_at'] = doc['created_at'].isoformat()
    doc['due_date'] = doc['due_date'].isoformat()
    await db.invoices.insert_one(doc)
    return invoice

@api_router.get("/invoices", response_model=List[Invoice])
async def get_invoices(status: Optional[str] = None):
    query = {}
    if status:
        query['status'] = status
    invoices = await db.invoices.find(query, {"_id": 0}).to_list(1000)
    for invoice in invoices:
        if isinstance(invoice.get('created_at'), str):
            invoice['created_at'] = datetime.fromisoformat(invoice['created_at'])
        if isinstance(invoice.get('due_date'), str):
            invoice['due_date'] = datetime.fromisoformat(invoice['due_date'])
    return invoices

@api_router.put("/invoices/{invoice_id}", response_model=Invoice)
async def update_invoice(invoice_id: str, invoice_input: InvoiceCreate):
    invoice_dict = invoice_input.model_dump()
    # Get client name
    client = await db.clients.find_one({"id": invoice_dict['client_id']}, {"_id": 0})
    if client:
        invoice_dict['client_name'] = client['name']
    invoice_dict['due_date'] = invoice_dict['due_date'].isoformat()
    result = await db.invoices.update_one({"id": invoice_id}, {"$set": invoice_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Invoice not found")
    updated_invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
    if isinstance(updated_invoice.get('created_at'), str):
        updated_invoice['created_at'] = datetime.fromisoformat(updated_invoice['created_at'])
    if isinstance(updated_invoice.get('due_date'), str):
        updated_invoice['due_date'] = datetime.fromisoformat(updated_invoice['due_date'])
    return updated_invoice

# Staff Routes
@api_router.post("/staff", response_model=Staff)
async def create_staff(staff_input: StaffCreate):
    staff_dict = staff_input.model_dump()
    staff = Staff(**staff_dict)
    doc = staff.model_dump()
    doc['joined_date'] = doc['joined_date'].isoformat()
    await db.staff.insert_one(doc)
    return staff

@api_router.get("/staff", response_model=List[Staff])
async def get_staff():
    staff_list = await db.staff.find({}, {"_id": 0}).to_list(1000)
    for staff in staff_list:
        if isinstance(staff.get('joined_date'), str):
            staff['joined_date'] = datetime.fromisoformat(staff['joined_date'])
    return staff_list

@api_router.delete("/staff/{staff_id}")
async def delete_staff(staff_id: str):
    result = await db.staff.delete_one({"id": staff_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Staff not found")
    return {"message": "Staff deleted successfully"}

# Dashboard Stats
@api_router.get("/dashboard/stats", response_model=DashboardStats)
async def get_dashboard_stats():
    # Count total clients
    total_clients = await db.clients.count_documents({"status": "ACTIVE"})
    
    # Count active tasks
    active_tasks = await db.tasks.count_documents({"status": {"$in": ["PENDING", "IN_PROGRESS"]}})
    
    # Count pending invoices
    pending_invoices = await db.invoices.count_documents({"status": {"$in": ["SENT", "OVERDUE"]}})
    
    # Calculate total revenue
    paid_invoices = await db.invoices.find({"status": "PAID"}, {"_id": 0}).to_list(1000)
    total_revenue = sum(invoice.get('total', 0) for invoice in paid_invoices)
    
    # Get upcoming deadlines (next 7 days)
    now = datetime.now(timezone.utc)
    upcoming_tasks = await db.tasks.find(
        {"status": {"$in": ["PENDING", "IN_PROGRESS"]}},
        {"_id": 0}
    ).sort("due_date", 1).limit(5).to_list(5)
    
    for task in upcoming_tasks:
        if isinstance(task.get('created_at'), str):
            task['created_at'] = datetime.fromisoformat(task['created_at'])
        if isinstance(task.get('due_date'), str):
            task['due_date'] = datetime.fromisoformat(task['due_date'])
    
    return DashboardStats(
        total_clients=total_clients,
        active_tasks=active_tasks,
        pending_invoices=pending_invoices,
        total_revenue=total_revenue,
        upcoming_deadlines=upcoming_tasks
    )

# ===== PRODUCTION FEATURES =====

# File Upload Routes
@api_router.post("/upload")
async def upload_file(
    file: UploadFile = File(...),
    category: str = "general",
    current_user: User = Depends(get_current_user)
):
    """Upload a file."""
    try:
        file_content = await file.read()
        result = file_service.save_file(file_content, file.filename, category)
        
        if result["success"]:
            return {
                "success": True,
                "file_url": result["file_url"],
                "filename": result["original_filename"]
            }
        else:
            raise HTTPException(status_code=500, detail=result["error"])
    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# PDF Generation Routes
@api_router.get("/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(
    invoice_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate and download invoice as PDF."""
    try:
        # Get invoice data
        invoice = await db.invoices.find_one({"id": invoice_id}, {"_id": 0})
        if not invoice:
            raise HTTPException(status_code=404, detail="Invoice not found")
        
        # Convert datetime fields
        if isinstance(invoice.get('due_date'), str):
            due_date = datetime.fromisoformat(invoice['due_date'])
            invoice['due_date'] = due_date.strftime('%B %d, %Y')
        
        # Generate PDF
        pdf_bytes = pdf_service.generate_invoice_pdf(invoice)
        
        # Return as downloadable file
        return StreamingResponse(
            iter([pdf_bytes]),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f"attachment; filename=invoice-{invoice['invoice_number']}.pdf"
            }
        )
    except Exception as e:
        logger.error(f"PDF generation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Email Notification Routes
@api_router.post("/notifications/deadline-reminder/{task_id}")
async def send_deadline_reminder_notification(
    task_id: str,
    current_user: User = Depends(get_current_user)
):
    """Send deadline reminder email for a task."""
    try:
        task = await db.tasks.find_one({"id": task_id}, {"_id": 0})
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        # Get client email
        client = await db.clients.find_one({"id": task['client_id']}, {"_id": 0})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        # Convert due_date
        due_date = task['due_date']
        if isinstance(due_date, str):
            due_date = datetime.fromisoformat(due_date)
        
        # Send email
        result = email_service.send_deadline_reminder(
            to=client['email'],
            task_name=task['title'],
            deadline=due_date,
            priority=task['priority']
        )
        
        return result
    except Exception as e:
        logger.error(f"Error sending reminder: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Reports Routes
@api_router.get("/reports/compliance")
async def get_compliance_report(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    current_user: User = Depends(get_current_user)
):
    """Generate compliance report."""
    try:
        query = {}
        if start_date and end_date:
            query['due_date'] = {
                '$gte': start_date,
                '$lte': end_date
            }
        
        tasks = await db.tasks.find(query, {"_id": 0}).to_list(1000)
        
        # Group by task type
        report = {
            "total_tasks": len(tasks),
            "by_type": {},
            "by_status": {},
            "overdue": 0
        }
        
        for task in tasks:
            task_type = task.get('task_type', 'GENERAL')
            status = task.get('status', 'PENDING')
            
            report['by_type'][task_type] = report['by_type'].get(task_type, 0) + 1
            report['by_status'][status] = report['by_status'].get(status, 0) + 1
            
            if status == 'OVERDUE':
                report['overdue'] += 1
        
        return report
    except Exception as e:
        logger.error(f"Error generating report: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Calendar View Route
@api_router.get("/calendar/tasks")
async def get_calendar_tasks(
    month: int,
    year: int,
    current_user: User = Depends(get_current_user)
):
    """Get tasks for calendar view by month and year."""
    try:
        # Create date range for the month
        from datetime import date
        from calendar import monthrange
        
        start_date = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end_date = date(year, month, last_day)
        
        # Query tasks
        tasks = await db.tasks.find({
            "due_date": {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        }, {"_id": 0}).to_list(1000)
        
        # Convert datetime strings
        for task in tasks:
            if isinstance(task.get('due_date'), str):
                task['due_date'] = datetime.fromisoformat(task['due_date'])
        
        return {"tasks": tasks, "month": month, "year": year}
    except Exception as e:
        logger.error(f"Error fetching calendar tasks: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Data Export Routes
@api_router.get("/export/clients")
async def export_clients_csv(current_user: User = Depends(get_current_user)):
    """Export clients as CSV."""
    import csv
    from io import StringIO
    
    try:
        clients = await db.clients.find({}, {"_id": 0}).to_list(1000)
        
        output = StringIO()
        if clients:
            writer = csv.DictWriter(output, fieldnames=clients[0].keys())
            writer.writeheader()
            writer.writerows(clients)
        
        csv_content = output.getvalue()
        output.close()
        
        return Response(
            content=csv_content,
            media_type="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=clients.csv"
            }
        )
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# ===== AUTOMATION FEATURES =====

# Bulk Import Routes
@api_router.post("/import/clients")
async def bulk_import_clients(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Bulk import clients from CSV."""
    try:
        file_content = await file.read()
        result = await bulk_import_service.import_clients_from_csv(file_content, db)
        return result
    except Exception as e:
        logger.error(f"Import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/import/tasks")
async def bulk_import_tasks(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    """Bulk import tasks from CSV."""
    try:
        file_content = await file.read()
        result = await bulk_import_service.import_tasks_from_csv(file_content, db)
        return result
    except Exception as e:
        logger.error(f"Import error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/import/templates/clients")
async def download_client_template(current_user: User = Depends(get_current_user)):
    """Download CSV template for client import."""
    template_bytes = bulk_import_service.generate_client_template()
    return Response(
        content=template_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=client_import_template.csv"}
    )

@api_router.get("/import/templates/tasks")
async def download_task_template(current_user: User = Depends(get_current_user)):
    """Download CSV template for task import."""
    template_bytes = bulk_import_service.generate_task_template()
    return Response(
        content=template_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=task_import_template.csv"}
    )

# Template-based Task Creation
@api_router.get("/templates/services")
async def get_service_templates(current_user: User = Depends(get_current_user)):
    """Get available service templates."""
    return {"templates": template_service.get_available_templates()}

@api_router.post("/templates/create-task")
async def create_task_from_template(
    template_name: str,
    client_id: str,
    custom_data: Optional[Dict] = None,
    current_user: User = Depends(get_current_user)
):
    """Create task from template."""
    try:
        # Get client
        client = await db.clients.find_one({"id": client_id}, {"_id": 0})
        if not client:
            raise HTTPException(status_code=404, detail="Client not found")
        
        result = await template_service.create_from_template(
            template_name=template_name,
            client_id=client_id,
            client_name=client['name'],
            db=db,
            custom_data=custom_data
        )
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Template task creation error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# Smart Document Upload with Auto-categorization
@api_router.post("/upload/smart")
async def smart_upload_file(
    file: UploadFile = File(...),
    client_id: str = None,
    current_user: User = Depends(get_current_user)
):
    """Upload file with automatic categorization."""
    try:
        # Auto-categorize
        category = document_intelligence.auto_categorize(file.filename)
        
        # Extract metadata
        metadata = document_intelligence.extract_metadata(file.filename)
        
        # Suggest tags
        tags = document_intelligence.suggest_tags(file.filename, category)
        
        # Save file
        file_content = await file.read()
        result = file_service.save_file(file_content, file.filename, category)
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result["error"])
        
        # Create document record
        doc = {
            "id": str(uuid.uuid4()),
            "client_id": client_id,
            "filename": file.filename,
            "file_url": result["file_url"],
            "category": category,
            "tags": tags,
            "metadata": metadata,
            "uploaded_at": datetime.now(timezone.utc).isoformat()
        }
        
        if client_id:
            client = await db.clients.find_one({\"id\": client_id}, {\"_id\": 0})
            if client:
                doc[\"client_name\"] = client['name']
        
        await db.documents.insert_one(doc)
        
        return {
            \"success\": True,
            \"file_url\": result[\"file_url\"],
            \"category\": category,
            \"tags\": tags,
            \"metadata\": metadata
        }
    except Exception as e:
        logger.error(f\"Smart upload error: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))

# Automation Control
@api_router.post("/automation/start")
async def start_automation(current_user: User = Depends(get_current_user)):
    """Start automated task generation and reminders."""
    try:
        automation_service.start_automation()
        return {
            \"success\": True,
            \"message\": \"Automation started successfully\",
            \"scheduled_jobs\": [
                \"Deadline reminders (daily at 9 AM)\",
                \"Recurring task generation (daily at midnight)\",
                \"Overdue task updates (hourly)\",
                \"Auto task assignment (daily at 8 AM)\"
            ]
        }
    except Exception as e:
        logger.error(f\"Automation start error: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/automation/stop")
async def stop_automation(current_user: User = Depends(get_current_user)):
    """Stop automation scheduler."""
    try:
        automation_service.shutdown()
        return {\"success\": True, \"message\": \"Automation stopped\"}
    except Exception as e:
        logger.error(f\"Automation stop error: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))

# Manual trigger for testing
@api_router.post("/automation/trigger/reminders")
async def trigger_reminders(current_user: User = Depends(get_current_user)):
    """Manually trigger deadline reminders."""
    try:
        await automation_service.send_deadline_reminders()
        return {\"success\": True, \"message\": \"Reminders sent\"}
    except Exception as e:
        logger.error(f\"Reminder trigger error: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/automation/trigger/recurring-tasks")
async def trigger_recurring_tasks(current_user: User = Depends(get_current_user)):
    """Manually trigger recurring task generation."""
    try:
        await automation_service.generate_recurring_tasks()
        return {\"success\": True, \"message\": \"Recurring tasks generated\"}
    except Exception as e:
        logger.error(f\"Recurring task trigger error: {str(e)}\")
        raise HTTPException(status_code=500, detail=str(e))

# Include auth router
app.include_router(auth_router, prefix="/api")

# Include the main API router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()