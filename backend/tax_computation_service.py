from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class TaxComputationService:
    """Service for tax computation as per Income Tax Act."""
    
    def __init__(self):
        # Tax slabs for FY 2024-25 (AY 2025-26)
        self.old_regime_slabs = [
            {'min': 0, 'max': 250000, 'rate': 0},
            {'min': 250000, 'max': 500000, 'rate': 0.05},
            {'min': 500000, 'max': 1000000, 'rate': 0.20},
            {'min': 1000000, 'max': float('inf'), 'rate': 0.30}
        ]
        
        self.new_regime_slabs = [
            {'min': 0, 'max': 300000, 'rate': 0},
            {'min': 300000, 'max': 600000, 'rate': 0.05},
            {'min': 600000, 'max': 900000, 'rate': 0.10},
            {'min': 900000, 'max': 1200000, 'rate': 0.15},
            {'min': 1200000, 'max': 1500000, 'rate': 0.20},
            {'min': 1500000, 'max': float('inf'), 'rate': 0.30}
        ]
        
        # Standard deduction (applicable in both regimes)
        self.standard_deduction = 50000
        
        # Depreciation rates as per IT Act
        self.depreciation_rates = {
            'building': 0.05,  # 5% for building
            'furniture': 0.10,  # 10% for furniture
            'plant_machinery': 0.15,  # 15% for plant & machinery
            'computers': 0.40,  # 40% for computers
            'vehicles': 0.15,  # 15% for vehicles
            'intangible': 0.25  # 25% for intangible assets
        }
    
    def calculate_income_tax(
        self,
        income_data: Dict[str, Any],
        regime: str = 'new'
    ) -> Dict[str, Any]:
        """Calculate income tax in specified regime."""
        try:
            # Extract income components
            gross_salary = income_data.get('gross_salary', 0)
            business_income = income_data.get('business_income', 0)
            house_property_income = income_data.get('house_property_income', 0)
            capital_gains_short = income_data.get('capital_gains_short_term', 0)
            capital_gains_long = income_data.get('capital_gains_long_term', 0)
            other_income = income_data.get('other_income', 0)
            
            # Calculate total income
            gross_total_income = (
                gross_salary + business_income + house_property_income +
                capital_gains_short + capital_gains_long + other_income
            )
            
            # Deductions (only in old regime)
            deductions_80c = income_data.get('deductions_80c', 0) if regime == 'old' else 0
            deductions_80d = income_data.get('deductions_80d', 0) if regime == 'old' else 0
            deductions_80g = income_data.get('deductions_80g', 0) if regime == 'old' else 0
            other_deductions = income_data.get('other_deductions', 0) if regime == 'old' else 0
            
            total_deductions = deductions_80c + deductions_80d + deductions_80g + other_deductions
            
            # Apply standard deduction
            taxable_income = gross_total_income - self.standard_deduction - total_deductions
            taxable_income = max(0, taxable_income)
            
            # Calculate tax based on regime
            slabs = self.new_regime_slabs if regime == 'new' else self.old_regime_slabs
            tax_on_income = self._calculate_tax_from_slabs(taxable_income, slabs)
            
            # Add 4% cess
            cess = tax_on_income * 0.04
            total_tax = tax_on_income + cess
            
            # Round to nearest rupee
            total_tax = round(total_tax)
            
            return {
                'success': True,
                'regime': regime,
                'gross_total_income': gross_total_income,
                'standard_deduction': self.standard_deduction,
                'total_deductions': total_deductions,
                'taxable_income': taxable_income,
                'tax_on_income': tax_on_income,
                'cess': cess,
                'total_tax_liability': total_tax,
                'effective_tax_rate': round((total_tax / gross_total_income * 100), 2) if gross_total_income > 0 else 0,
                'tax_breakdown': self._get_tax_breakdown(taxable_income, slabs)
            }
        except Exception as e:
            logger.error(f"Error calculating income tax: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def compare_regimes(
        self,
        income_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Compare tax liability in both regimes and recommend."""
        old_regime_result = self.calculate_income_tax(income_data, 'old')
        new_regime_result = self.calculate_income_tax(income_data, 'new')
        
        if old_regime_result['success'] and new_regime_result['success']:
            old_tax = old_regime_result['total_tax_liability']
            new_tax = new_regime_result['total_tax_liability']
            
            savings = abs(old_tax - new_tax)
            recommended = 'new' if new_tax < old_tax else 'old'
            
            return {
                'success': True,
                'old_regime': old_regime_result,
                'new_regime': new_regime_result,
                'recommended_regime': recommended,
                'tax_savings': savings,
                'savings_percentage': round((savings / max(old_tax, new_tax) * 100), 2) if max(old_tax, new_tax) > 0 else 0,
                'recommendation_reason': self._get_recommendation_reason(old_tax, new_tax, income_data)
            }
        else:
            return {'success': False, 'error': 'Failed to compare regimes'}
    
    def calculate_depreciation(
        self,
        assets: List[Dict[str, Any]],
        method: str = 'wdv'  # Written Down Value
    ) -> Dict[str, Any]:
        """Calculate depreciation as per Income Tax Act."""
        try:
            depreciation_schedule = []
            total_depreciation = 0
            
            for asset in assets:
                asset_type = asset.get('type', 'plant_machinery')
                opening_wdv = asset.get('opening_wdv', 0)
                additions = asset.get('additions', 0)
                
                # Get depreciation rate
                rate = self.depreciation_rates.get(asset_type, 0.15)
                
                # Calculate depreciation
                if method == 'wdv':  # Written Down Value method
                    depreciation = (opening_wdv + additions) * rate
                else:  # Straight Line Method (rarely used in IT Act)
                    depreciation = (opening_wdv / asset.get('useful_life', 10))
                
                closing_wdv = opening_wdv + additions - depreciation
                
                depreciation_schedule.append({
                    'asset_name': asset.get('name', 'Unnamed Asset'),
                    'asset_type': asset_type,
                    'opening_wdv': opening_wdv,
                    'additions': additions,
                    'depreciation_rate': rate * 100,
                    'depreciation': round(depreciation, 2),
                    'closing_wdv': round(closing_wdv, 2)
                })
                
                total_depreciation += depreciation
            
            return {
                'success': True,
                'method': method,
                'depreciation_schedule': depreciation_schedule,
                'total_depreciation': round(total_depreciation, 2)
            }
        except Exception as e:
            logger.error(f"Error calculating depreciation: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_capital_gains(
        self,
        transaction: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate capital gains (short-term and long-term)."""
        try:
            asset_type = transaction.get('asset_type', 'equity')  # equity, property, etc.
            purchase_price = transaction.get('purchase_price', 0)
            sale_price = transaction.get('sale_price', 0)
            purchase_date = transaction.get('purchase_date')
            sale_date = transaction.get('sale_date')
            
            # Calculate holding period
            if purchase_date and sale_date:
                holding_days = (sale_date - purchase_date).days
            else:
                holding_days = transaction.get('holding_days', 0)
            
            # Determine if short-term or long-term
            if asset_type == 'equity':
                is_long_term = holding_days > 365  # > 1 year for equity
            elif asset_type == 'property':
                is_long_term = holding_days > 730  # > 2 years for property
            else:
                is_long_term = holding_days > 1095  # > 3 years for other assets
            
            # Calculate indexed cost for long-term property
            indexed_cost = purchase_price
            if is_long_term and asset_type == 'property':
                cii_purchase = transaction.get('cost_inflation_index_purchase', 100)
                cii_sale = transaction.get('cost_inflation_index_sale', 110)
                indexed_cost = purchase_price * (cii_sale / cii_purchase)
            
            # Calculate capital gain
            capital_gain = sale_price - indexed_cost
            
            # Calculate tax
            if is_long_term:
                if asset_type == 'equity':
                    # LTCG on equity: 10% above 1 lakh
                    exempt_amount = 100000
                    taxable_gain = max(0, capital_gain - exempt_amount)
                    tax = taxable_gain * 0.10
                elif asset_type == 'property':
                    # LTCG on property: 20% with indexation
                    tax = capital_gain * 0.20
                else:
                    tax = capital_gain * 0.20
            else:
                # STCG: Added to income and taxed at slab rates
                # Or 15% for equity (if listed)
                if asset_type == 'equity':
                    tax = capital_gain * 0.15
                else:
                    tax = 0  # Will be added to total income
            
            return {
                'success': True,
                'asset_type': asset_type,
                'holding_period_days': holding_days,
                'is_long_term': is_long_term,
                'purchase_price': purchase_price,
                'sale_price': sale_price,
                'indexed_cost': round(indexed_cost, 2),
                'capital_gain': round(capital_gain, 2),
                'tax_on_capital_gain': round(tax, 2),
                'type': 'Long-term' if is_long_term else 'Short-term'
            }
        except Exception as e:
            logger.error(f"Error calculating capital gains: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_gst_liability(
        self,
        transactions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate GST liability for a period."""
        try:
            output_gst = 0  # GST collected on sales
            input_gst = 0   # GST paid on purchases
            
            for txn in transactions:
                txn_type = txn.get('type', 'sale')  # sale or purchase
                amount = txn.get('amount', 0)
                gst_rate = txn.get('gst_rate', 0.18)  # 18% default
                
                gst_amount = amount * gst_rate
                
                if txn_type == 'sale':
                    output_gst += gst_amount
                else:  # purchase
                    input_gst += gst_amount
            
            # GST liability = Output GST - Input Tax Credit
            gst_liability = output_gst - input_gst
            
            # Split into CGST and SGST (50-50)
            cgst = gst_liability / 2
            sgst = gst_liability / 2
            
            return {
                'success': True,
                'output_gst': round(output_gst, 2),
                'input_gst': round(input_gst, 2),
                'input_tax_credit': round(input_gst, 2),
                'net_gst_liability': round(gst_liability, 2),
                'cgst': round(cgst, 2),
                'sgst': round(sgst, 2),
                'payment_required': gst_liability > 0,
                'refund_due': gst_liability < 0,
                'refund_amount': round(abs(gst_liability), 2) if gst_liability < 0 else 0
            }
        except Exception as e:
            logger.error(f"Error calculating GST: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def calculate_tds(
        self,
        payment_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate TDS to be deducted."""
        try:
            payment_type = payment_data.get('type', 'professional_fees')  # salary, professional_fees, rent, etc.
            amount = payment_data.get('amount', 0)
            
            # TDS rates
            tds_rates = {
                'salary': 0,  # As per slab
                'professional_fees': 0.10,  # 10% (Section 194J)
                'contract': 0.02,  # 2% (Section 194C) - Individual/HUF
                'contract_company': 0.01,  # 1% (Section 194C) - Company
                'rent': 0.10,  # 10% (Section 194I)
                'commission': 0.05,  # 5% (Section 194H)
                'interest': 0.10,  # 10% (Section 194A)
                'dividend': 0.10  # 10% (Section 194)
            }
            
            tds_rate = tds_rates.get(payment_type, 0.10)
            tds_amount = amount * tds_rate
            
            # Check threshold limits
            thresholds = {
                'professional_fees': 30000,
                'rent': 240000,  # Per year
                'commission': 15000,
                'interest': 40000  # For bank interest
            }
            
            threshold = thresholds.get(payment_type, 0)
            tds_applicable = amount >= threshold
            
            return {
                'success': True,
                'payment_type': payment_type,
                'amount': amount,
                'tds_rate': tds_rate * 100,
                'tds_amount': round(tds_amount, 2) if tds_applicable else 0,
                'tds_applicable': tds_applicable,
                'threshold': threshold,
                'net_payment': round(amount - (tds_amount if tds_applicable else 0), 2)
            }
        except Exception as e:
            logger.error(f"Error calculating TDS: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    def _calculate_tax_from_slabs(self, income: float, slabs: List[Dict]) -> float:
        """Calculate tax based on slab rates."""
        tax = 0
        for slab in slabs:
            if income > slab['min']:
                taxable_in_slab = min(income, slab['max']) - slab['min']
                tax += taxable_in_slab * slab['rate']
        return tax
    
    def _get_tax_breakdown(self, income: float, slabs: List[Dict]) -> List[Dict]:
        """Get detailed tax breakdown by slabs."""
        breakdown = []
        for slab in slabs:
            if income > slab['min']:
                taxable_in_slab = min(income, slab['max']) - slab['min']
                tax_in_slab = taxable_in_slab * slab['rate']
                if taxable_in_slab > 0:
                    breakdown.append({
                        'slab': f"₹{slab['min']:,} - ₹{slab['max']:,}" if slab['max'] != float('inf') else f"₹{slab['min']:,} and above",
                        'rate': slab['rate'] * 100,
                        'taxable_amount': round(taxable_in_slab, 2),
                        'tax': round(tax_in_slab, 2)
                    })
        return breakdown
    
    def _get_recommendation_reason(self, old_tax: float, new_tax: float, income_data: Dict) -> str:
        """Get reason for regime recommendation."""
        deductions = income_data.get('deductions_80c', 0) + income_data.get('deductions_80d', 0)
        
        if new_tax < old_tax:
            return f"New regime saves ₹{old_tax - new_tax:,}. Lower tax rates compensate for loss of deductions."
        else:
            return f"Old regime saves ₹{new_tax - old_tax:,}. Your deductions (₹{deductions:,}) provide significant benefit."

# Global tax computation service
tax_computation_service = TaxComputationService()
