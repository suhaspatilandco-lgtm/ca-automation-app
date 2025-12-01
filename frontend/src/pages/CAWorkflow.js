import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Building2, Calendar, CheckCircle2, MessageSquare, AlertTriangle, Shield } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const CAWorkflow = () => {
  const [businessTypes, setBusinessTypes] = useState([]);
  const [wipStages, setWipStages] = useState([]);
  const [currentFY, setCurrentFY] = useState(null);
  const [currentQuarter, setCurrentQuarter] = useState(null);
  const [selectedBusiness, setSelectedBusiness] = useState('');
  const [turnover, setTurnover] = useState('');
  const [compliance, setCompliance] = useState(null);
  const [gstin, setGstin] = useState('');
  const [gstinValidation, setGstinValidation] = useState(null);
  const [pan, setPan] = useState('');
  const [panValidation, setPanValidation] = useState(null);
  const [lateFee, setLateFee] = useState(null);

  useEffect(() => {
    fetchCAData();
  }, []);

  const fetchCAData = async () => {
    try {
      const [btRes, wsRes, fyRes, qRes] = await Promise.all([
        axios.get(`${API}/ca/business-types`),
        axios.get(`${API}/ca/wip-stages`),
        axios.get(`${API}/ca/financial-year`),
        axios.get(`${API}/ca/quarter`)
      ]);
      
      setBusinessTypes(btRes.data.business_types || []);
      setWipStages(wsRes.data.stages || []);
      setCurrentFY(fyRes.data);
      setCurrentQuarter(qRes.data);
    } catch (error) {
      console.error('Error fetching CA data:', error);
      toast.error('Failed to load CA workflow data');
    }
  };

  const handleComplianceCheck = async () => {
    if (!selectedBusiness) {
      toast.error('Please select a business type');
      return;
    }

    try {
      const response = await axios.post(`${API}/ca/compliance-requirements`, null, {
        params: {
          business_type: selectedBusiness,
          turnover: turnover ? parseFloat(turnover) : null
        }
      });
      setCompliance(response.data);
      toast.success('Compliance requirements loaded');
    } catch (error) {
      console.error('Error checking compliance:', error);
      toast.error('Failed to check compliance');
    }
  };

  const validateGSTIN = async () => {
    if (!gstin) return;
    try {
      const response = await axios.post(`${API}/ca/validate-gstin`, null, {
        params: { gstin }
      });
      setGstinValidation(response.data);
      if (response.data.valid) {
        toast.success('Valid GSTIN');
      } else {
        toast.error(response.data.error);
      }
    } catch (error) {
      toast.error('Validation failed');
    }
  };

  const validatePAN = async () => {
    if (!pan) return;
    try {
      const response = await axios.post(`${API}/ca/validate-pan`, null, {
        params: { pan }
      });
      setPanValidation(response.data);
      if (response.data.valid) {
        toast.success('Valid PAN');
      } else {
        toast.error(response.data.error);
      }
    } catch (error) {
      toast.error('Validation failed');
    }
  };

  const calculateLateFee = async () => {
    try {
      const dueDate = new Date();
      dueDate.setDate(dueDate.getDate() - 30); // 30 days overdue example
      
      const response = await axios.post(`${API}/ca/calculate-late-fee`, null, {
        params: {
          task_type: 'GST',
          due_date: dueDate.toISOString()
        }
      });
      setLateFee(response.data);
    } catch (error) {
      toast.error('Failed to calculate late fee');
    }
  };

  return (
    <div className="space-y-6 page-enter" data-testid="ca-workflow-page">
      {/* Header */}
      <div className="bg-gradient-to-r from-slate-900 to-slate-800 rounded-xl p-6 text-white">
        <h1 className="text-3xl font-bold mb-2">CA Workflow Management</h1>
        <p className="text-slate-300">Advanced tools for CA practice automation</p>
      </div>

      {/* Financial Year Info */}
      {currentFY && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Calendar className="w-4 h-4 text-emerald-600" />
                Current Financial Year
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">{currentFY.fy_code}</div>
              <p className="text-xs text-slate-500 mt-1">Assessment Year: {currentFY.ay_code}</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <CheckCircle2 className="w-4 h-4 text-blue-600" />
                Current Quarter
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">
                {currentQuarter?.quarter_label}
              </div>
              <p className="text-xs text-slate-500 mt-1">Quarter {currentQuarter?.quarter} of 4</p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Building2 className="w-4 h-4 text-purple-600" />
                WIP Stages
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-slate-900">{wipStages.length}</div>
              <p className="text-xs text-slate-500 mt-1">Workflow stages available</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Business Type Compliance Checker */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Shield className="w-5 h-5 text-emerald-600" />
            Compliance Requirements Checker
          </CardTitle>
          <CardDescription>Check compliance requirements based on business type</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Business Type</label>
              <Select value={selectedBusiness} onValueChange={setSelectedBusiness}>
                <SelectTrigger>
                  <SelectValue placeholder="Select type" />
                </SelectTrigger>
                <SelectContent>
                  {businessTypes.map(type => (
                    <SelectItem key={type} value={type}>{type.replace('_', ' ')}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Annual Turnover (₹)</label>
              <input
                type="number"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="e.g., 5000000"
                value={turnover}
                onChange={(e) => setTurnover(e.target.value)}
              />
            </div>
            <div className="flex items-end">
              <Button onClick={handleComplianceCheck} className="w-full bg-emerald-600 hover:bg-emerald-700">
                Check Compliance
              </Button>
            </div>
          </div>

          {compliance && (
            <div className="mt-4 p-4 bg-slate-50 rounded-lg">
              <h3 className="font-semibold mb-3">Required Compliance:</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                <Badge variant={compliance.requires_gst ? "default" : "secondary"}>
                  GST: {compliance.requires_gst ? 'Required' : 'Not Required'}
                </Badge>
                <Badge variant={compliance.requires_audit ? "default" : "secondary"}>
                  Audit: {compliance.requires_audit ? 'Required' : 'Not Required'}
                </Badge>
                <Badge variant={compliance.requires_tds ? "default" : "secondary"}>
                  TDS: {compliance.requires_tds ? 'Required' : 'Not Required'}
                </Badge>
                <Badge variant={compliance.requires_roc_filing ? "default" : "secondary"}>
                  ROC: {compliance.requires_roc_filing ? 'Required' : 'Not Required'}
                </Badge>
              </div>
              {compliance.applicable_returns && (
                <div className="mt-3">
                  <p className="text-sm text-slate-600">Applicable Returns:</p>
                  <div className="flex gap-2 mt-2">
                    {compliance.applicable_returns.map(ret => (
                      <Badge key={ret} className="bg-emerald-100 text-emerald-700">{ret}</Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Validation Tools */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* GSTIN Validator */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">GSTIN Validator</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <input
                type="text"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Enter GSTIN (15 characters)"
                value={gstin}
                onChange={(e) => setGstin(e.target.value.toUpperCase())}
                maxLength={15}
              />
            </div>
            <Button onClick={validateGSTIN} className="w-full" variant="outline">
              Validate GSTIN
            </Button>
            {gstinValidation && (
              <div className={`p-3 rounded ${gstinValidation.valid ? 'bg-green-50' : 'bg-red-50'}`}>
                {gstinValidation.valid ? (
                  <div className="text-sm">
                    <p className="font-semibold text-green-700">✓ Valid GSTIN</p>
                    <p className="text-green-600 mt-1">State Code: {gstinValidation.state_code}</p>
                    <p className="text-green-600">PAN: {gstinValidation.pan}</p>
                  </div>
                ) : (
                  <p className="text-red-700 text-sm">✗ {gstinValidation.error}</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>

        {/* PAN Validator */}
        <Card>
          <CardHeader>
            <CardTitle className="text-lg">PAN Validator</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            <div>
              <input
                type="text"
                className="w-full px-3 py-2 border rounded-md"
                placeholder="Enter PAN (10 characters)"
                value={pan}
                onChange={(e) => setPan(e.target.value.toUpperCase())}
                maxLength={10}
              />
            </div>
            <Button onClick={validatePAN} className="w-full" variant="outline">
              Validate PAN
            </Button>
            {panValidation && (
              <div className={`p-3 rounded ${panValidation.valid ? 'bg-green-50' : 'bg-red-50'}`}>
                {panValidation.valid ? (
                  <div className="text-sm">
                    <p className="font-semibold text-green-700">✓ Valid PAN</p>
                    <p className="text-green-600 mt-1">Entity Type: {panValidation.entity_type}</p>
                  </div>
                ) : (
                  <p className="text-red-700 text-sm">✗ {panValidation.error}</p>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Late Fee Calculator */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-600" />
            Late Fee Calculator
          </CardTitle>
          <CardDescription>Calculate penalties for missed deadlines</CardDescription>
        </CardHeader>
        <CardContent>
          <Button onClick={calculateLateFee} className="bg-amber-600 hover:bg-amber-700">
            Calculate GST Late Fee (30 days overdue example)
          </Button>
          {lateFee && (
            <div className="mt-4 p-4 bg-amber-50 rounded-lg border border-amber-200">
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-xs text-slate-600">Days Overdue</p>
                  <p className="text-2xl font-bold text-amber-700">{lateFee.days_overdue}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Late Fee</p>
                  <p className="text-2xl font-bold text-amber-700">₹{lateFee.late_fee}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Interest</p>
                  <p className="text-2xl font-bold text-amber-700">₹{lateFee.interest.toFixed(2)}</p>
                </div>
                <div>
                  <p className="text-xs text-slate-600">Total Penalty</p>
                  <p className="text-2xl font-bold text-red-700">₹{lateFee.total_penalty}</p>
                </div>
              </div>
            </div>
          )}
        </CardContent>
      </Card>

      {/* WIP Stages Overview */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <MessageSquare className="w-5 h-5 text-blue-600" />
            Work-in-Progress Stages
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-2">
            {wipStages.map((stage, index) => (
              <div key={stage} className="flex items-center gap-2">
                <Badge className="bg-blue-100 text-blue-700">
                  {index + 1}. {stage.replace('_', ' ')}
                </Badge>
                {index < wipStages.length - 1 && <span className="text-slate-400">→</span>}
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default CAWorkflow;