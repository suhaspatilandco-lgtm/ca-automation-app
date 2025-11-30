import pandas as pd
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any
import logging
from io import BytesIO

logger = logging.getLogger(__name__)

class BulkImportService:
    
    async def import_clients_from_csv(self, file_content: bytes, db) -> Dict[str, Any]:
        """Import clients from CSV file."""
        try:
            # Read CSV
            df = pd.read_csv(BytesIO(file_content))
            
            # Expected columns
            required_columns = ['name', 'email', 'phone']
            optional_columns = ['gstin', 'pan', 'address', 'status']
            
            # Validate required columns
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing)}"
                }
            
            # Process each row
            imported = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Check if client already exists
                    existing = await db.clients.find_one({"email": row['email']})
                    if existing:
                        errors.append(f"Row {index + 2}: Client with email {row['email']} already exists")
                        continue
                    
                    # Create client document
                    client = {
                        "id": str(uuid.uuid4()),
                        "name": str(row['name']),
                        "email": str(row['email']),
                        "phone": str(row['phone']),
                        "gstin": str(row.get('gstin', '')) if pd.notna(row.get('gstin')) else None,
                        "pan": str(row.get('pan', '')) if pd.notna(row.get('pan')) else None,
                        "address": str(row.get('address', '')) if pd.notna(row.get('address')) else None,
                        "status": str(row.get('status', 'ACTIVE')),
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await db.clients.insert_one(client)
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            return {
                "success": True,
                "imported": imported,
                "total_rows": len(df),
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error importing clients: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def import_tasks_from_csv(self, file_content: bytes, db) -> Dict[str, Any]:
        """Import tasks from CSV file."""
        try:
            df = pd.read_csv(BytesIO(file_content))
            
            required_columns = ['title', 'client_email', 'task_type', 'due_date']
            missing = [col for col in required_columns if col not in df.columns]
            if missing:
                return {
                    "success": False,
                    "error": f"Missing required columns: {', '.join(missing)}"
                }
            
            imported = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Find client by email
                    client = await db.clients.find_one(
                        {"email": row['client_email']},
                        {"_id": 0}
                    )
                    
                    if not client:
                        errors.append(f"Row {index + 2}: Client not found for email {row['client_email']}")
                        continue
                    
                    # Parse due date
                    due_date = pd.to_datetime(row['due_date'])
                    
                    # Create task
                    task = {
                        "id": str(uuid.uuid4()),
                        "title": str(row['title']),
                        "description": str(row.get('description', '')) if pd.notna(row.get('description')) else None,
                        "client_id": client['id'],
                        "client_name": client['name'],
                        "task_type": str(row['task_type']).upper(),
                        "due_date": due_date.isoformat(),
                        "status": str(row.get('status', 'PENDING')).upper(),
                        "priority": str(row.get('priority', 'MEDIUM')).upper(),
                        "assigned_to": str(row.get('assigned_to', '')) if pd.notna(row.get('assigned_to')) else None,
                        "created_at": datetime.now(timezone.utc).isoformat()
                    }
                    
                    await db.tasks.insert_one(task)
                    imported += 1
                    
                except Exception as e:
                    errors.append(f"Row {index + 2}: {str(e)}")
            
            return {
                "success": True,
                "imported": imported,
                "total_rows": len(df),
                "errors": errors if errors else None
            }
            
        except Exception as e:
            logger.error(f"Error importing tasks: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def generate_client_template(self) -> bytes:
        """Generate CSV template for client import."""
        template_data = {
            'name': ['ABC Enterprises', 'XYZ Ltd'],
            'email': ['abc@example.com', 'xyz@example.com'],
            'phone': ['9876543210', '9876543211'],
            'gstin': ['29ABCDE1234F1Z5', '27XYZAB5678G2H9'],
            'pan': ['ABCDE1234F', 'XYZAB5678G'],
            'address': ['123 Street, Mumbai', '456 Road, Delhi'],
            'status': ['ACTIVE', 'ACTIVE']
        }
        
        df = pd.DataFrame(template_data)
        output = BytesIO()
        df.to_csv(output, index=False)
        return output.getvalue()
    
    def generate_task_template(self) -> bytes:
        """Generate CSV template for task import."""
        template_data = {
            'title': ['GST Filing Q1', 'ITR Filing FY 2024-25'],
            'client_email': ['abc@example.com', 'xyz@example.com'],
            'task_type': ['GST', 'ITR'],
            'due_date': ['2025-04-20', '2025-07-31'],
            'description': ['Quarterly GST return', 'Annual tax filing'],
            'status': ['PENDING', 'PENDING'],
            'priority': ['HIGH', 'URGENT'],
            'assigned_to': ['', '']
        }
        
        df = pd.DataFrame(template_data)
        output = BytesIO()
        df.to_csv(output, index=False)
        return output.getvalue()

# Global bulk import service
bulk_import_service = BulkImportService()