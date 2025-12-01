import pdfplumber
import re
from typing import Dict, Any, List, Optional
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

class OCRService:
    """OCR service for extracting data from documents."""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.png', '.jpg', '.jpeg']
    
    def extract_form16(self, file_path: str) -> Dict[str, Any]:
        """Extract data from Form 16 (Salary TDS Certificate)."""
        try:
            text = self._extract_text_from_pdf(file_path)
            
            extracted = {
                'document_type': 'Form 16',
                'employer_name': self._extract_employer_name(text),
                'employer_pan': self._extract_pan(text),
                'employee_name': self._extract_employee_name(text),
                'employee_pan': self._extract_pan(text, is_employee=True),
                'financial_year': self._extract_fy(text),
                'gross_salary': self._extract_amount(text, 'gross salary'),
                'total_deductions': self._extract_amount(text, 'total deductions'),
                'taxable_income': self._extract_amount(text, 'taxable income'),
                'tax_deducted': self._extract_amount(text, 'tax deducted', 'tds'),
                'quarters': self._extract_quarterly_tds(text)
            }
            
            return {
                'success': True,
                'data': extracted,
                'confidence': self._calculate_confidence(extracted)
            }
        except Exception as e:
            logger.error(f"Error extracting Form 16: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_invoice(self, file_path: str) -> Dict[str, Any]:
        """Extract data from invoice/bill."""
        try:
            text = self._extract_text_from_pdf(file_path)
            
            extracted = {
                'document_type': 'Invoice',
                'invoice_number': self._extract_invoice_number(text),
                'invoice_date': self._extract_date(text),
                'vendor_name': self._extract_vendor_name(text),
                'vendor_gstin': self._extract_gstin(text),
                'buyer_gstin': self._extract_buyer_gstin(text),
                'items': self._extract_line_items(text),
                'subtotal': self._extract_amount(text, 'subtotal', 'sub total'),
                'cgst': self._extract_amount(text, 'cgst'),
                'sgst': self._extract_amount(text, 'sgst'),
                'igst': self._extract_amount(text, 'igst'),
                'total_amount': self._extract_amount(text, 'total', 'grand total', 'invoice total'),
                'hsn_codes': self._extract_hsn_codes(text)
            }
            
            return {
                'success': True,
                'data': extracted,
                'confidence': self._calculate_confidence(extracted)
            }
        except Exception as e:
            logger.error(f"Error extracting invoice: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_bank_statement(self, file_path: str) -> Dict[str, Any]:
        """Extract transactions from bank statement."""
        try:
            text = self._extract_text_from_pdf(file_path)
            
            extracted = {
                'document_type': 'Bank Statement',
                'bank_name': self._extract_bank_name(text),
                'account_number': self._extract_account_number(text),
                'statement_period': self._extract_statement_period(text),
                'opening_balance': self._extract_amount(text, 'opening balance'),
                'closing_balance': self._extract_amount(text, 'closing balance'),
                'transactions': self._extract_transactions(text)
            }
            
            return {
                'success': True,
                'data': extracted,
                'confidence': self._calculate_confidence(extracted)
            }
        except Exception as e:
            logger.error(f"Error extracting bank statement: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def extract_challan(self, file_path: str) -> Dict[str, Any]:
        """Extract data from tax payment challan."""
        try:
            text = self._extract_text_from_pdf(file_path)
            
            extracted = {
                'document_type': 'Challan',
                'challan_number': self._extract_challan_number(text),
                'payment_date': self._extract_date(text),
                'pan': self._extract_pan(text),
                'assessment_year': self._extract_ay(text),
                'tax_type': self._extract_tax_type(text),
                'amount_paid': self._extract_amount(text, 'amount', 'paid'),
                'bank_name': self._extract_bank_name(text)
            }
            
            return {
                'success': True,
                'data': extracted,
                'confidence': self._calculate_confidence(extracted)
            }
        except Exception as e:
            logger.error(f"Error extracting challan: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    def _extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF using pdfplumber."""
        text = ""
        with pdfplumber.open(file_path) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        return text
    
    def _extract_pan(self, text: str, is_employee: bool = False) -> Optional[str]:
        """Extract PAN number."""
        pan_pattern = r'\b[A-Z]{5}[0-9]{4}[A-Z]\b'
        matches = re.findall(pan_pattern, text)
        if matches:
            # If multiple PANs, second one is usually employee's in Form 16
            return matches[1] if is_employee and len(matches) > 1 else matches[0]
        return None
    
    def _extract_gstin(self, text: str) -> Optional[str]:
        """Extract GSTIN."""
        gstin_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b'
        match = re.search(gstin_pattern, text)
        return match.group(0) if match else None
    
    def _extract_amount(self, text: str, *keywords) -> Optional[float]:
        """Extract amount based on keywords."""
        for keyword in keywords:
            pattern = rf'{keyword}[:\s]*[₹Rs.]*\s*([\d,]+(?:\.\d{{2}})?)'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                amount_str = match.group(1).replace(',', '')
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        return None
    
    def _extract_date(self, text: str) -> Optional[str]:
        """Extract date in various formats."""
        date_patterns = [
            r'\b\d{2}[/-]\d{2}[/-]\d{4}\b',  # DD/MM/YYYY or DD-MM-YYYY
            r'\b\d{4}[/-]\d{2}[/-]\d{2}\b',  # YYYY-MM-DD
            r'\b\d{2}\s+[A-Za-z]{3}\s+\d{4}\b'  # DD Mon YYYY
        ]
        for pattern in date_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(0)
        return None
    
    def _extract_employer_name(self, text: str) -> Optional[str]:
        """Extract employer name from Form 16."""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'employer' in line.lower() and i + 1 < len(lines):
                return lines[i + 1].strip()
        return None
    
    def _extract_employee_name(self, text: str) -> Optional[str]:
        """Extract employee name from Form 16."""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if 'employee' in line.lower() and 'name' in line.lower() and i + 1 < len(lines):
                return lines[i + 1].strip()
        return None
    
    def _extract_fy(self, text: str) -> Optional[str]:
        """Extract Financial Year."""
        fy_pattern = r'FY\s*\d{4}-\d{2}|\d{4}-\d{4}'
        match = re.search(fy_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None
    
    def _extract_ay(self, text: str) -> Optional[str]:
        """Extract Assessment Year."""
        ay_pattern = r'AY\s*\d{4}-\d{2}'
        match = re.search(ay_pattern, text, re.IGNORECASE)
        return match.group(0) if match else None
    
    def _extract_quarterly_tds(self, text: str) -> List[Dict[str, Any]]:
        """Extract quarterly TDS breakdown from Form 16."""
        quarters = []
        quarter_pattern = r'Q(\d).*?([\d,]+(?:\.\d{2})?)'
        matches = re.findall(quarter_pattern, text)
        for quarter_num, amount in matches:
            quarters.append({
                'quarter': f"Q{quarter_num}",
                'tds_amount': float(amount.replace(',', ''))
            })
        return quarters
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extract invoice number."""
        patterns = [
            r'invoice\s*(?:no|number|#)[:\s]*([A-Z0-9/-]+)',
            r'bill\s*(?:no|number)[:\s]*([A-Z0-9/-]+)'
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        return None
    
    def _extract_vendor_name(self, text: str) -> Optional[str]:
        """Extract vendor/seller name."""
        lines = text.split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['seller', 'vendor', 'from']):
                if i + 1 < len(lines):
                    return lines[i + 1].strip()
        return None
    
    def _extract_buyer_gstin(self, text: str) -> Optional[str]:
        """Extract buyer GSTIN (second GSTIN in invoice)."""
        gstin_pattern = r'\b\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}Z[A-Z\d]{1}\b'
        matches = re.findall(gstin_pattern, text)
        return matches[1] if len(matches) > 1 else None
    
    def _extract_line_items(self, text: str) -> List[Dict[str, Any]]:
        """Extract line items from invoice."""
        # Simplified extraction - looks for patterns like:
        # Description  Qty  Rate  Amount
        items = []
        lines = text.split('\n')
        in_items_section = False
        
        for line in lines:
            if any(kw in line.lower() for kw in ['description', 'item', 'particulars']):
                in_items_section = True
                continue
            if in_items_section and any(kw in line.lower() for kw in ['subtotal', 'total', 'cgst']):
                break
            if in_items_section:
                # Try to extract amounts from line
                amounts = re.findall(r'([\d,]+(?:\.\d{2})?)', line)
                if len(amounts) >= 2:
                    items.append({
                        'description': line.split(amounts[0])[0].strip(),
                        'quantity': float(amounts[0].replace(',', '')) if len(amounts) > 0 else 1,
                        'rate': float(amounts[1].replace(',', '')) if len(amounts) > 1 else 0,
                        'amount': float(amounts[-1].replace(',', '')) if amounts else 0
                    })
        
        return items
    
    def _extract_hsn_codes(self, text: str) -> List[str]:
        """Extract HSN codes."""
        hsn_pattern = r'\b\d{4,8}\b'  # HSN codes are 4-8 digits
        matches = re.findall(hsn_pattern, text)
        # Filter out numbers that are too large or small to be HSN
        return [m for m in matches if 1000 <= int(m) <= 99999999]
    
    def _extract_bank_name(self, text: str) -> Optional[str]:
        """Extract bank name."""
        banks = ['HDFC', 'ICICI', 'SBI', 'Axis', 'Kotak', 'IDBI', 'PNB', 'Bank of Baroda', 'Canara']
        for bank in banks:
            if bank.lower() in text.lower():
                return bank
        return None
    
    def _extract_account_number(self, text: str) -> Optional[str]:
        """Extract bank account number."""
        pattern = r'account\s*(?:no|number)[:\s]*(\d{9,18})'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_statement_period(self, text: str) -> Optional[str]:
        """Extract statement period."""
        pattern = r'(?:from|period)[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})\s*(?:to)[:\s]*(\d{2}[/-]\d{2}[/-]\d{4})'
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return f"{match.group(1)} to {match.group(2)}"
        return None
    
    def _extract_transactions(self, text: str) -> List[Dict[str, Any]]:
        """Extract bank transactions."""
        transactions = []
        lines = text.split('\n')
        
        for line in lines:
            # Look for lines with date and amount pattern
            date_match = re.search(r'\d{2}[/-]\d{2}[/-]\d{4}', line)
            if date_match:
                amounts = re.findall(r'([\d,]+(?:\.\d{2})?)', line)
                if amounts:
                    transactions.append({
                        'date': date_match.group(0),
                        'description': line.split(date_match.group(0))[1].split(amounts[0])[0].strip(),
                        'debit': float(amounts[0].replace(',', '')) if 'dr' in line.lower() or 'debit' in line.lower() else 0,
                        'credit': float(amounts[0].replace(',', '')) if 'cr' in line.lower() or 'credit' in line.lower() else 0,
                        'balance': float(amounts[-1].replace(',', '')) if len(amounts) > 1 else 0
                    })
        
        return transactions
    
    def _extract_challan_number(self, text: str) -> Optional[str]:
        """Extract challan number."""
        pattern = r'challan\s*(?:no|number)[:\s]*([\d/-]+)'
        match = re.search(pattern, text, re.IGNORECASE)
        return match.group(1) if match else None
    
    def _extract_tax_type(self, text: str) -> Optional[str]:
        """Extract tax type from challan."""
        tax_types = ['advance tax', 'self assessment', 'tds', 'tcs', 'regular assessment']
        text_lower = text.lower()
        for tax_type in tax_types:
            if tax_type in text_lower:
                return tax_type.title()
        return None
    
    def _calculate_confidence(self, extracted: Dict[str, Any]) -> float:
        """Calculate extraction confidence score."""
        total_fields = len(extracted)
        filled_fields = sum(1 for v in extracted.values() if v is not None and v != '' and v != [])
        return round((filled_fields / total_fields) * 100, 2) if total_fields > 0 else 0.0

# Global OCR service
ocr_service = OCRService()
