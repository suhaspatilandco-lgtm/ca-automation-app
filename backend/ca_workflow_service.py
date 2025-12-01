from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
import logging
from ca_workflow_models import (
    BusinessType, WIPStage, QueryStatus,
    COMPLIANCE_MATRIX, SERVICE_CHECKLISTS,
    FinancialYear
)

logger = logging.getLogger(__name__)

class CAWorkflowService:
    """Service for CA-specific workflow management."""
    
    def get_financial_year(self, date: datetime = None) -> Dict[str, Any]:
        """Get current or specified financial year."""
        if not date:
            date = datetime.now(timezone.utc)
        
        # FY starts on April 1st
        if date.month >= 4:
            fy_start_year = date.year
            fy_end_year = date.year + 1
        else:
            fy_start_year = date.year - 1
            fy_end_year = date.year
        
        fy_code = f"FY{fy_start_year}-{str(fy_end_year)[2:]}"
        ay_code = f"AY{fy_end_year}-{str(fy_end_year + 1)[2:]}"
        
        return {
            "fy_code": fy_code,
            "ay_code": ay_code,
            "start_date": datetime(fy_start_year, 4, 1, tzinfo=timezone.utc),
            "end_date": datetime(fy_end_year, 3, 31, 23, 59, tzinfo=timezone.utc),
            "current": True
        }
    
    def get_quarter(self, date: datetime = None) -> int:
        """Get current quarter (1-4) for given date."""
        if not date:
            date = datetime.now(timezone.utc)
        
        # FY starts in April, so Q1 = Apr-Jun, Q2 = Jul-Sep, etc.
        month = date.month
        if month in [4, 5, 6]:
            return 1
        elif month in [7, 8, 9]:
            return 2
        elif month in [10, 11, 12]:
            return 3
        else:  # 1, 2, 3
            return 4
    
    def determine_compliance_requirements(
        self,
        business_type: BusinessType,
        turnover: Optional[float] = None
    ) -> Dict[str, Any]:
        """Determine compliance requirements based on business type and turnover."""
        
        if business_type not in COMPLIANCE_MATRIX:
            logger.warning(f"Unknown business type: {business_type}")
            return {}
        
        requirements = COMPLIANCE_MATRIX[business_type].copy()
        
        # Handle conditional requirements based on turnover
        if turnover:
            # GST registration required if turnover > 40 lakhs (goods) or 20 lakhs (services)
            if requirements["requires_gst"] == "conditional":
                requirements["requires_gst"] = turnover > 4000000  # 40 lakhs
            
            # Audit required if turnover > 1 crore for proprietorship/partnership
            if requirements["requires_audit"] == "conditional":
                requirements["requires_audit"] = turnover > 10000000  # 1 crore
            
            # TDS applicable if certain payments exceed threshold
            if requirements["requires_tds"] == "conditional":
                requirements["requires_tds"] = turnover > 5000000  # 50 lakhs (rough estimate)
        
        return requirements
    
    def get_service_checklist(self, service_type: str) -> List[Dict[str, Any]]:
        """Get detailed checklist for a service type."""
        return SERVICE_CHECKLISTS.get(service_type, [])
    
    def calculate_late_fee(
        self,
        task_type: str,
        due_date: datetime,
        current_date: datetime = None
    ) -> Dict[str, Any]:
        """Calculate late fee for missed compliance deadlines."""
        
        if not current_date:
            current_date = datetime.now(timezone.utc)
        
        if current_date <= due_date:
            return {
                "late_fee": 0,
                "interest": 0,
                "total_penalty": 0,
                "days_overdue": 0,
                "overdue": False
            }
        
        days_overdue = (current_date - due_date).days
        
        # Late fee calculation based on task type
        late_fees = {
            "GST": {
                "daily_fee": 50,  # ₹50 per day (₹25 CGST + ₹25 SGST)
                "max_fee": 5000,
                "interest_rate": 0.18  # 18% per annum
            },
            "ITR": {
                "flat_fee": 5000 if days_overdue <= 365 else 10000,
                "interest_rate": 0.01  # 1% per month
            },
            "TDS": {
                "daily_fee": 200,  # ₹200 per day
                "interest_rate": 0.015  # 1.5% per month
            },
            "ROC": {
                "daily_fee": 100,  # ₹100 per day
                "max_fee": 200000
            },
            "AUDIT": {
                "flat_fee": 0,  # No late fee, but ITR filing delayed
                "interest_rate": 0
            }
        }
        
        fee_structure = late_fees.get(task_type, {"daily_fee": 0, "interest_rate": 0})
        
        # Calculate late fee
        if "daily_fee" in fee_structure:
            late_fee = min(
                days_overdue * fee_structure["daily_fee"],
                fee_structure.get("max_fee", float('inf'))
            )
        elif "flat_fee" in fee_structure:
            late_fee = fee_structure["flat_fee"]
        else:
            late_fee = 0
        
        # Calculate interest (simplified calculation)
        interest_rate = fee_structure.get("interest_rate", 0)
        # Assuming average tax liability of ₹10,000 for interest calculation
        assumed_liability = 10000
        interest = (assumed_liability * interest_rate * days_overdue) / 365
        
        return {
            "late_fee": round(late_fee, 2),
            "interest": round(interest, 2),
            "total_penalty": round(late_fee + interest, 2),
            "days_overdue": days_overdue,
            "overdue": True,
            "penalty_breakdown": {
                "late_fee_per_day": fee_structure.get("daily_fee", 0),
                "interest_rate_pa": interest_rate * 100,
                "assumed_tax_liability": assumed_liability
            }
        }
    
    def get_wip_stage_sequence(self) -> List[str]:
        """Get the sequence of WIP stages."""
        return [
            WIPStage.DATA_COLLECTION,
            WIPStage.UNDER_PREPARATION,
            WIPStage.REVIEW,
            WIPStage.CLIENT_APPROVAL,
            WIPStage.FILING,
            WIPStage.ACKNOWLEDGMENT_RECEIVED,
            WIPStage.COMPLETED
        ]
    
    def advance_wip_stage(self, current_stage: WIPStage) -> WIPStage:
        """Advance to next WIP stage."""
        stages = self.get_wip_stage_sequence()
        current_index = stages.index(current_stage)
        
        if current_index < len(stages) - 1:
            return stages[current_index + 1]
        return current_stage  # Already at final stage
    
    def calculate_query_aging(self, raised_at: datetime, current_date: datetime = None) -> int:
        """Calculate how many days a query has been pending."""
        if not current_date:
            current_date = datetime.now(timezone.utc)
        
        return (current_date - raised_at).days
    
    def should_send_query_reminder(self, query: Dict[str, Any]) -> bool:
        """Determine if a query reminder should be sent."""
        days_pending = query.get('days_pending', 0)
        reminders_sent = query.get('reminders_sent', 0)
        
        # Send reminder after 3, 7, 14 days
        reminder_days = [3, 7, 14]
        
        if reminders_sent < len(reminder_days) and days_pending >= reminder_days[reminders_sent]:
            return True
        
        return False
    
    def get_applicable_task_types(self, business_type: BusinessType, turnover: Optional[float] = None) -> List[str]:
        """Get list of applicable task types for a business."""
        requirements = self.determine_compliance_requirements(business_type, turnover)
        return requirements.get('applicable_returns', [])
    
    def validate_gstin(self, gstin: str) -> Dict[str, Any]:
        """Validate GSTIN format and extract information."""
        if not gstin or len(gstin) != 15:
            return {"valid": False, "error": "GSTIN must be 15 characters"}
        
        # GSTIN format: 2 digits state code + 10 chars PAN + 1 entity code + Z + 1 checksum
        state_code = gstin[:2]
        pan = gstin[2:12]
        entity_code = gstin[12]
        
        if not state_code.isdigit():
            return {"valid": False, "error": "Invalid state code"}
        
        if gstin[13] != 'Z':
            return {"valid": False, "error": "13th character must be Z"}
        
        return {
            "valid": True,
            "state_code": state_code,
            "pan": pan,
            "entity_code": entity_code,
            "checksum": gstin[14]
        }
    
    def validate_pan(self, pan: str) -> Dict[str, Any]:
        """Validate PAN format."""
        if not pan or len(pan) != 10:
            return {"valid": False, "error": "PAN must be 10 characters"}
        
        # PAN format: 5 letters + 4 digits + 1 letter
        if not pan[:5].isalpha() or not pan[5:9].isdigit() or not pan[9].isalpha():
            return {"valid": False, "error": "Invalid PAN format"}
        
        # 4th character indicates entity type
        entity_type_map = {
            'P': 'Individual',
            'C': 'Company',
            'H': 'HUF',
            'F': 'Firm',
            'A': 'AOP',
            'T': 'Trust',
            'B': 'BOI',
            'L': 'Local Authority',
            'J': 'Artificial Juridical Person',
            'G': 'Government'
        }
        
        entity_type = entity_type_map.get(pan[3], 'Unknown')
        
        return {
            "valid": True,
            "entity_type": entity_type,
            "pan": pan.upper()
        }

# Global service instance
ca_workflow_service = CAWorkflowService()
