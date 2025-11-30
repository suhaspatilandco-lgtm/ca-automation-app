from typing import Dict, Any, List
from datetime import datetime, timedelta, timezone
import uuid
import logging

logger = logging.getLogger(__name__)

class TemplateService:
    """Quick-entry templates for common CA services."""
    
    def __init__(self):
        self.service_templates = {
            "GST_MONTHLY": {
                "title_pattern": "GSTR-3B Filing - {month} {year}",
                "description": "Monthly GST return filing",
                "task_type": "GST",
                "priority": "HIGH",
                "due_date_rule": "20th of next month",
                "checklist": [
                    "Collect sales invoices",
                    "Collect purchase invoices",
                    "Verify GSTR-2A",
                    "Prepare GSTR-3B",
                    "File return",
                    "Save acknowledgment"
                ]
            },
            "GST_QUARTERLY": {
                "title_pattern": "GSTR-1 Filing - Q{quarter} {fy}",
                "description": "Quarterly GST return filing",
                "task_type": "GST",
                "priority": "HIGH",
                "due_date_rule": "13th of month after quarter",
                "checklist": [
                    "Collect all invoices for quarter",
                    "Verify details",
                    "Upload invoices",
                    "File GSTR-1"
                ]
            },
            "ITR_INDIVIDUAL": {
                "title_pattern": "ITR Filing - FY {fy}",
                "description": "Individual Income Tax Return",
                "task_type": "ITR",
                "priority": "URGENT",
                "due_date_rule": "31st July",
                "checklist": [
                    "Collect Form 16",
                    "Bank statements",
                    "Investment proofs (80C, 80D)",
                    "House property details",
                    "Other income details",
                    "Compute tax",
                    "File ITR",
                    "Verify return"
                ]
            },
            "ITR_BUSINESS": {
                "title_pattern": "ITR Filing - Business - FY {fy}",
                "description": "Business/Professional Income Tax Return",
                "task_type": "ITR",
                "priority": "URGENT",
                "due_date_rule": "31st October",
                "checklist": [
                    "Finalize books of accounts",
                    "Prepare P&L and Balance Sheet",
                    "Tax audit report (if applicable)",
                    "Compute income and tax",
                    "File ITR",
                    "Pay advance tax/self-assessment"
                ]
            },
            "TDS_QUARTERLY": {
                "title_pattern": "TDS Return - Q{quarter} {fy}",
                "description": "Quarterly TDS return filing",
                "task_type": "GENERAL",
                "priority": "HIGH",
                "due_date_rule": "31st of month after quarter",
                "checklist": [
                    "Collect TDS challan details",
                    "Prepare deductee details",
                    "Download FVU",
                    "Upload TDS return",
                    "Generate Form 16/16A"
                ]
            },
            "AUDIT": {
                "title_pattern": "Tax Audit - FY {fy}",
                "description": "Annual tax audit",
                "task_type": "AUDIT",
                "priority": "URGENT",
                "due_date_rule": "30th September",
                "checklist": [
                    "Collect books of accounts",
                    "Prepare trial balance",
                    "Verify transactions",
                    "Check compliance",
                    "Draft audit report",
                    "Finalize and sign",
                    "Upload audit report"
                ]
            },
            "ROC_ANNUAL": {
                "title_pattern": "ROC Annual Filing - FY {fy}",
                "description": "Annual return and financial statements filing with ROC",
                "task_type": "ROC",
                "priority": "URGENT",
                "due_date_rule": "30th November",
                "checklist": [
                    "Board meeting for accounts approval",
                    "AGM notice",
                    "Conduct AGM",
                    "Prepare AOC-4",
                    "Prepare MGT-7",
                    "File with ROC"
                ]
            }
        }
    
    async def create_from_template(
        self,
        template_name: str,
        client_id: str,
        client_name: str,
        db,
        custom_data: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Create task from template with smart date calculation."""
        try:
            template = self.service_templates.get(template_name)
            if not template:
                return {
                    "success": False,
                    "error": f"Template '{template_name}' not found"
                }
            
            now = datetime.now(timezone.utc)
            custom_data = custom_data or {}
            
            # Calculate due date based on rule
            due_date = self._calculate_due_date(template["due_date_rule"], now)
            
            # Generate title with current period
            title = self._generate_title(template["title_pattern"], now)
            
            # Create task
            task = {
                "id": str(uuid.uuid4()),
                "title": custom_data.get("title", title),
                "description": custom_data.get("description", template["description"]),
                "client_id": client_id,
                "client_name": client_name,
                "task_type": template["task_type"],
                "due_date": due_date.isoformat(),
                "status": "PENDING",
                "priority": custom_data.get("priority", template["priority"]),
                "assigned_to": custom_data.get("assigned_to"),
                "created_at": now.isoformat(),
                "template_used": template_name,
                "checklist": template["checklist"]
            }
            
            await db.tasks.insert_one(task)
            
            return {
                "success": True,
                "task": task
            }
            
        except Exception as e:
            logger.error(f"Error creating task from template: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def _calculate_due_date(self, rule: str, ref_date: datetime) -> datetime:
        """Calculate due date based on rule."""
        if "20th of next month" in rule:
            # Next month, 20th day
            next_month = ref_date.replace(day=1) + timedelta(days=32)
            return next_month.replace(day=20, hour=23, minute=59)
        
        elif "31st July" in rule:
            # July 31st of current year if before July, else next year
            year = ref_date.year if ref_date.month <= 7 else ref_date.year + 1
            return datetime(year, 7, 31, 23, 59, tzinfo=timezone.utc)
        
        elif "31st October" in rule:
            # October 31st
            year = ref_date.year if ref_date.month <= 10 else ref_date.year + 1
            return datetime(year, 10, 31, 23, 59, tzinfo=timezone.utc)
        
        elif "30th September" in rule:
            # September 30th
            year = ref_date.year if ref_date.month <= 9 else ref_date.year + 1
            return datetime(year, 9, 30, 23, 59, tzinfo=timezone.utc)
        
        elif "30th November" in rule:
            # November 30th
            year = ref_date.year if ref_date.month <= 11 else ref_date.year + 1
            return datetime(year, 11, 30, 23, 59, tzinfo=timezone.utc)
        
        elif "31st of month after quarter" in rule:
            # End of month after current quarter
            current_quarter = (ref_date.month - 1) // 3
            quarter_end_month = (current_quarter + 1) * 3
            due_month = quarter_end_month + 1
            due_year = ref_date.year if due_month <= 12 else ref_date.year + 1
            due_month = due_month if due_month <= 12 else due_month - 12
            return datetime(due_year, due_month, 31, 23, 59, tzinfo=timezone.utc)
        
        else:
            # Default: 30 days from now
            return ref_date + timedelta(days=30)
    
    def _generate_title(self, pattern: str, ref_date: datetime) -> str:
        """Generate title from pattern."""
        replacements = {
            "{month}": ref_date.strftime("%B"),
            "{year}": str(ref_date.year),
            "{fy}": self._get_fy(ref_date),
            "{quarter}": str((ref_date.month - 1) // 3 + 1)
        }
        
        title = pattern
        for key, value in replacements.items():
            title = title.replace(key, value)
        
        return title
    
    def _get_fy(self, ref_date: datetime) -> str:
        """Get financial year in format 2024-25."""
        if ref_date.month >= 4:
            return f"{ref_date.year}-{str(ref_date.year + 1)[2:]}"
        else:
            return f"{ref_date.year - 1}-{str(ref_date.year)[2:]}"
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """Get list of available templates."""
        return [
            {
                "name": name,
                "title_pattern": template["title_pattern"],
                "description": template["description"],
                "task_type": template["task_type"],
                "checklist_items": len(template["checklist"])
            }
            for name, template in self.service_templates.items()
        ]

# Global template service
template_service = TemplateService()