import logging
import re
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)

class DocumentIntelligence:
    """Smart document categorization and data extraction."""
    
    def __init__(self):
        # Category keywords mapping
        self.category_keywords = {
            "GST": ["gst", "gstin", "gstr", "goods and services tax", "invoice"],
            "ITR": ["itr", "income tax", "form 16", "26as", "tds certificate"],
            "Audit": ["audit", "auditor", "financial statement", "balance sheet"],
            "ROC": ["roc", "mca", "annual return", "aoc", "mgt"],
            "Financial": ["bank statement", "ledger", "trial balance", "p&l", "profit"],
            "Legal": ["agreement", "contract", "mou", "legal", "court"],
            "General": []
        }
    
    def auto_categorize(self, filename: str, content: Optional[bytes] = None) -> str:
        """Auto-categorize document based on filename and content."""
        try:
            filename_lower = filename.lower()
            
            # Check filename against keywords
            for category, keywords in self.category_keywords.items():
                for keyword in keywords:
                    if keyword in filename_lower:
                        logger.info(f"Auto-categorized '{filename}' as {category}")
                        return category
            
            # Default category
            return "General"
            
        except Exception as e:
            logger.error(f"Error in auto-categorization: {str(e)}")
            return "General"
    
    def extract_metadata(self, filename: str) -> Dict[str, Any]:
        """Extract metadata from filename."""
        try:
            metadata = {
                "original_name": filename,
                "extension": Path(filename).suffix,
                "detected_type": None,
                "detected_period": None
            }
            
            filename_lower = filename.lower()
            
            # Detect document type
            if "invoice" in filename_lower:
                metadata["detected_type"] = "Invoice"
            elif "receipt" in filename_lower:
                metadata["detected_type"] = "Receipt"
            elif "statement" in filename_lower:
                metadata["detected_type"] = "Statement"
            elif "return" in filename_lower:
                metadata["detected_type"] = "Return"
            
            # Extract year/month patterns
            year_match = re.search(r'20\d{2}', filename)
            if year_match:
                metadata["detected_period"] = year_match.group(0)
            
            # Extract month
            months = [
                "jan", "feb", "mar", "apr", "may", "jun",
                "jul", "aug", "sep", "oct", "nov", "dec"
            ]
            for month in months:
                if month in filename_lower:
                    metadata["detected_month"] = month.capitalize()
                    break
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error extracting metadata: {str(e)}")
            return {"original_name": filename}
    
    def suggest_tags(self, filename: str, category: str) -> list:
        """Suggest tags based on filename and category."""
        tags = [category]
        filename_lower = filename.lower()
        
        # Add year as tag if found
        year_match = re.search(r'20\d{2}', filename)
        if year_match:
            tags.append(f"FY{year_match.group(0)}")
        
        # Add quarter if detected
        for i in range(1, 5):
            if f"q{i}" in filename_lower or f"quarter {i}" in filename_lower:
                tags.append(f"Q{i}")
                break
        
        # Add document type tags
        if "draft" in filename_lower:
            tags.append("Draft")
        if "final" in filename_lower:
            tags.append("Final")
        if "revised" in filename_lower:
            tags.append("Revised")
        
        return tags
    
    def extract_gstin_from_text(self, text: str) -> Optional[str]:
        """Extract GSTIN from text content."""
        # GSTIN format: 2 digits state code + 10 alphanumeric + 1 check digit + 1 Z + 1 alphanumeric
        pattern = r'\d{2}[A-Z]{5}\d{4}[A-Z]{1}[A-Z\d]{1}[Z]{1}[A-Z\d]{1}'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def extract_pan_from_text(self, text: str) -> Optional[str]:
        """Extract PAN from text content."""
        # PAN format: 5 letters + 4 digits + 1 letter
        pattern = r'[A-Z]{5}\d{4}[A-Z]{1}'
        match = re.search(pattern, text)
        return match.group(0) if match else None
    
    def extract_amounts(self, text: str) -> list:
        """Extract monetary amounts from text."""
        # Match patterns like: Rs. 1000, ₹1,00,000, 50000.00
        patterns = [
            r'(?:Rs\.?|₹)\s*([\d,]+(?:\.\d{2})?)',
            r'\b(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\b'
        ]
        
        amounts = []
        for pattern in patterns:
            matches = re.findall(pattern, text)
            amounts.extend(matches)
        
        return [amt.replace(',', '') for amt in amounts if amt]

# Global document intelligence service
document_intelligence = DocumentIntelligence()