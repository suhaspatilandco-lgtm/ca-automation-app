#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any

class CASystemTester:
    def __init__(self, base_url="https://ca-test-assist.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.created_entities = {
            'clients': [],
            'tasks': [],
            'documents': [],
            'invoices': [],
            'staff': []
        }

    def log_test(self, name: str, success: bool, details: str = ""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details:
            print(f"   Details: {details}")

    def make_request(self, method: str, endpoint: str, data: Dict = None, expected_status: int = 200) -> tuple:
        """Make HTTP request and return success status and response data"""
        url = f"{self.api_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)
            else:
                return False, f"Unsupported method: {method}"

            success = response.status_code == expected_status
            
            if success:
                try:
                    return True, response.json()
                except:
                    return True, response.text
            else:
                return False, f"Status {response.status_code}, Expected {expected_status}. Response: {response.text[:200]}"
                
        except requests.exceptions.RequestException as e:
            return False, f"Request failed: {str(e)}"

    def test_api_health(self):
        """Test basic API connectivity"""
        success, data = self.make_request('GET', '')
        self.log_test("API Health Check", success, str(data) if not success else "")
        return success

    def test_client_crud(self):
        """Test complete Client CRUD operations"""
        print("\n🔍 Testing Client Management...")
        
        # Test Create Client
        client_data = {
            "name": "Test Client Ltd",
            "email": "test@client.com",
            "phone": "+91-9876543210",
            "gstin": "29ABCDE1234F1Z5",
            "pan": "ABCDE1234F",
            "address": "123 Test Street, Mumbai",
            "status": "ACTIVE"
        }
        
        success, response = self.make_request('POST', 'clients', client_data, 200)
        self.log_test("Create Client", success, str(response) if not success else "")
        
        if success:
            client_id = response.get('id')
            self.created_entities['clients'].append(client_id)
            
            # Test Get Client
            success, response = self.make_request('GET', f'clients/{client_id}')
            self.log_test("Get Client by ID", success, str(response) if not success else "")
            
            # Test Update Client
            update_data = client_data.copy()
            update_data['name'] = "Updated Test Client Ltd"
            success, response = self.make_request('PUT', f'clients/{client_id}', update_data)
            self.log_test("Update Client", success, str(response) if not success else "")
            
            # Test Get All Clients
            success, response = self.make_request('GET', 'clients')
            self.log_test("Get All Clients", success and isinstance(response, list), 
                         str(response) if not success else f"Found {len(response)} clients")
            
            # Test Filter Clients by Status
            success, response = self.make_request('GET', 'clients?status=ACTIVE')
            self.log_test("Filter Clients by Status", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} active clients")
            
            return client_id
        return None

    def test_task_crud(self, client_id: str = None):
        """Test complete Task CRUD operations"""
        print("\n🔍 Testing Task Management...")
        
        if not client_id:
            print("⚠️  Skipping task tests - no client available")
            return None
            
        # Test Create Task
        due_date = (datetime.now() + timedelta(days=7)).isoformat()
        task_data = {
            "title": "GST Return Filing",
            "description": "Monthly GST return for Test Client",
            "client_id": client_id,
            "task_type": "GST",
            "due_date": due_date,
            "status": "PENDING",
            "priority": "HIGH",
            "assigned_to": "CA John Doe"
        }
        
        success, response = self.make_request('POST', 'tasks', task_data, 200)
        self.log_test("Create Task", success, str(response) if not success else "")
        
        if success:
            task_id = response.get('id')
            self.created_entities['tasks'].append(task_id)
            
            # Test Get Task
            success, response = self.make_request('GET', f'tasks/{task_id}')
            self.log_test("Get Task by ID", success, str(response) if not success else "")
            
            # Test Update Task Status
            update_data = task_data.copy()
            update_data['status'] = "IN_PROGRESS"
            success, response = self.make_request('PUT', f'tasks/{task_id}', update_data)
            self.log_test("Update Task Status", success, str(response) if not success else "")
            
            # Test Get All Tasks
            success, response = self.make_request('GET', 'tasks')
            self.log_test("Get All Tasks", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} tasks")
            
            # Test Filter Tasks by Type
            success, response = self.make_request('GET', 'tasks?task_type=GST')
            self.log_test("Filter Tasks by Type", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} GST tasks")
            
            # Test Filter Tasks by Status
            success, response = self.make_request('GET', 'tasks?status=IN_PROGRESS')
            self.log_test("Filter Tasks by Status", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} in-progress tasks")
            
            return task_id
        return None

    def test_document_crud(self, client_id: str = None):
        """Test complete Document CRUD operations"""
        print("\n🔍 Testing Document Management...")
        
        if not client_id:
            print("⚠️  Skipping document tests - no client available")
            return None
            
        # Test Create Document
        doc_data = {
            "client_id": client_id,
            "filename": "GST_Certificate_2024.pdf",
            "file_url": "https://example.com/docs/gst_cert_2024.pdf",
            "category": "GST"
        }
        
        success, response = self.make_request('POST', 'documents', doc_data, 200)
        self.log_test("Create Document", success, str(response) if not success else "")
        
        if success:
            doc_id = response.get('id')
            self.created_entities['documents'].append(doc_id)
            
            # Test Get All Documents
            success, response = self.make_request('GET', 'documents')
            self.log_test("Get All Documents", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} documents")
            
            # Test Filter Documents by Client
            success, response = self.make_request('GET', f'documents?client_id={client_id}')
            self.log_test("Filter Documents by Client", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} client documents")
            
            return doc_id
        return None

    def test_invoice_crud(self, client_id: str = None):
        """Test complete Invoice CRUD operations"""
        print("\n🔍 Testing Invoice Management...")
        
        if not client_id:
            print("⚠️  Skipping invoice tests - no client available")
            return None
            
        # Test Create Invoice
        due_date = (datetime.now() + timedelta(days=30)).isoformat()
        invoice_data = {
            "client_id": client_id,
            "invoice_number": "INV-2024-001",
            "items": [
                {
                    "description": "GST Return Filing Service",
                    "quantity": 1,
                    "rate": 5000.0,
                    "amount": 5000.0
                },
                {
                    "description": "Tax Consultation",
                    "quantity": 2,
                    "rate": 2000.0,
                    "amount": 4000.0
                }
            ],
            "subtotal": 9000.0,
            "tax": 1620.0,  # 18% GST
            "total": 10620.0,
            "status": "DRAFT",
            "due_date": due_date
        }
        
        success, response = self.make_request('POST', 'invoices', invoice_data, 200)
        self.log_test("Create Invoice", success, str(response) if not success else "")
        
        if success:
            invoice_id = response.get('id')
            self.created_entities['invoices'].append(invoice_id)
            
            # Test Update Invoice Status
            update_data = invoice_data.copy()
            update_data['status'] = "SENT"
            success, response = self.make_request('PUT', f'invoices/{invoice_id}', update_data)
            self.log_test("Update Invoice Status", success, str(response) if not success else "")
            
            # Test Get All Invoices
            success, response = self.make_request('GET', 'invoices')
            self.log_test("Get All Invoices", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} invoices")
            
            # Test Filter Invoices by Status
            success, response = self.make_request('GET', 'invoices?status=SENT')
            self.log_test("Filter Invoices by Status", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} sent invoices")
            
            return invoice_id
        return None

    def test_staff_crud(self):
        """Test complete Staff CRUD operations"""
        print("\n🔍 Testing Staff Management...")
        
        # Test Create Staff
        staff_data = {
            "name": "John Doe",
            "email": "john.doe@caoffice.com",
            "role": "Senior Associate",
            "phone": "+91-9876543211"
        }
        
        success, response = self.make_request('POST', 'staff', staff_data, 200)
        self.log_test("Create Staff", success, str(response) if not success else "")
        
        if success:
            staff_id = response.get('id')
            self.created_entities['staff'].append(staff_id)
            
            # Test Get All Staff
            success, response = self.make_request('GET', 'staff')
            self.log_test("Get All Staff", success and isinstance(response, list),
                         str(response) if not success else f"Found {len(response)} staff members")
            
            return staff_id
        return None

    def test_dashboard_stats(self):
        """Test Dashboard Statistics"""
        print("\n🔍 Testing Dashboard Statistics...")
        
        success, response = self.make_request('GET', 'dashboard/stats')
        self.log_test("Get Dashboard Stats", success, str(response) if not success else "")
        
        if success:
            required_fields = ['total_clients', 'active_tasks', 'pending_invoices', 'total_revenue', 'upcoming_deadlines']
            missing_fields = [field for field in required_fields if field not in response]
            
            if missing_fields:
                self.log_test("Dashboard Stats Structure", False, f"Missing fields: {missing_fields}")
            else:
                self.log_test("Dashboard Stats Structure", True, f"All required fields present")
                
                # Validate data types
                stats_valid = (
                    isinstance(response['total_clients'], int) and
                    isinstance(response['active_tasks'], int) and
                    isinstance(response['pending_invoices'], int) and
                    isinstance(response['total_revenue'], (int, float)) and
                    isinstance(response['upcoming_deadlines'], list)
                )
                
                self.log_test("Dashboard Stats Data Types", stats_valid, 
                             f"Stats: {response}" if not stats_valid else "All data types correct")

    def cleanup_test_data(self):
        """Clean up created test data"""
        print("\n🧹 Cleaning up test data...")
        
        # Delete in reverse order to handle dependencies
        for doc_id in self.created_entities['documents']:
            success, _ = self.make_request('DELETE', f'documents/{doc_id}', expected_status=200)
            self.log_test(f"Delete Document {doc_id}", success)
            
        for task_id in self.created_entities['tasks']:
            success, _ = self.make_request('DELETE', f'tasks/{task_id}', expected_status=200)
            self.log_test(f"Delete Task {task_id}", success)
            
        for invoice_id in self.created_entities['invoices']:
            # Note: No delete endpoint for invoices in the API, this is expected to fail
            pass
            
        for staff_id in self.created_entities['staff']:
            success, _ = self.make_request('DELETE', f'staff/{staff_id}', expected_status=200)
            self.log_test(f"Delete Staff {staff_id}", success)
            
        for client_id in self.created_entities['clients']:
            success, _ = self.make_request('DELETE', f'clients/{client_id}', expected_status=200)
            self.log_test(f"Delete Client {client_id}", success)

    def run_all_tests(self):
        """Run complete test suite"""
        print("🚀 Starting CA Practice Automation Backend Tests")
        print(f"🌐 Testing API at: {self.api_url}")
        print("=" * 60)
        
        # Test API connectivity first
        if not self.test_api_health():
            print("❌ API is not accessible. Stopping tests.")
            return False
            
        # Run CRUD tests
        client_id = self.test_client_crud()
        task_id = self.test_task_crud(client_id)
        doc_id = self.test_document_crud(client_id)
        invoice_id = self.test_invoice_crud(client_id)
        staff_id = self.test_staff_crud()
        
        # Test dashboard
        self.test_dashboard_stats()
        
        # Cleanup
        self.cleanup_test_data()
        
        # Print summary
        print("\n" + "=" * 60)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        success_rate = (self.tests_passed / self.tests_run * 100) if self.tests_run > 0 else 0
        print(f"📈 Success Rate: {success_rate:.1f}%")
        
        if success_rate >= 80:
            print("✅ Backend tests PASSED - System is working well!")
            return True
        else:
            print("❌ Backend tests FAILED - Multiple issues found")
            return False

def main():
    tester = CASystemTester()
    success = tester.run_all_tests()
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())