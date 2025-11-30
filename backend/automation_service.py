from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta, timezone
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import uuid
from typing import List, Dict, Any
from email_service import email_service

logger = logging.getLogger(__name__)

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'test_database')]

class AutomationService:
    def __init__(self):
        self.scheduler = AsyncIOScheduler()
        self.scheduler.start()
        logger.info("Automation scheduler started")
    
    def start_automation(self):
        """Start all automation jobs."""
        # Check for upcoming deadlines every day at 9 AM
        self.scheduler.add_job(
            self.send_deadline_reminders,
            'cron',
            hour=9,
            minute=0,
            id='deadline_reminders'
        )
        
        # Generate recurring tasks every day at midnight
        self.scheduler.add_job(
            self.generate_recurring_tasks,
            'cron',
            hour=0,
            minute=0,
            id='recurring_tasks'
        )
        
        # Update overdue tasks every hour
        self.scheduler.add_job(
            self.update_overdue_tasks,
            'interval',
            hours=1,
            id='overdue_tasks'
        )
        
        # Auto-assign unassigned tasks daily
        self.scheduler.add_job(
            self.auto_assign_tasks,
            'cron',
            hour=8,
            minute=0,
            id='auto_assign'
        )
        
        logger.info("All automation jobs scheduled")
    
    async def send_deadline_reminders(self):
        """Send reminders for tasks due in 1, 3, and 7 days."""
        try:
            now = datetime.now(timezone.utc)
            
            # Tasks due in 1, 3, and 7 days
            for days_ahead in [1, 3, 7]:
                target_date = now + timedelta(days=days_ahead)
                
                # Find tasks due on target date
                tasks = await db.tasks.find({
                    "status": {"$in": ["PENDING", "IN_PROGRESS"]},
                    "due_date": {
                        "$gte": target_date.replace(hour=0, minute=0).isoformat(),
                        "$lt": target_date.replace(hour=23, minute=59).isoformat()
                    }
                }, {"_id": 0}).to_list(100)
                
                for task in tasks:
                    # Get client email
                    client = await db.clients.find_one(
                        {"id": task['client_id']},
                        {"_id": 0}
                    )
                    
                    if client and client.get('email'):
                        # Send reminder
                        due_date = datetime.fromisoformat(task['due_date'])
                        email_service.send_deadline_reminder(
                            to=client['email'],
                            task_name=task['title'],
                            deadline=due_date,
                            priority=task['priority']
                        )
                        
                        logger.info(
                            f"Reminder sent for task {task['id']} "
                            f"({days_ahead} days before deadline)"
                        )
            
            logger.info("Deadline reminders sent successfully")
        except Exception as e:
            logger.error(f"Error sending deadline reminders: {str(e)}")
    
    async def generate_recurring_tasks(self):
        """Auto-generate recurring compliance tasks."""
        try:
            now = datetime.now(timezone.utc)
            clients = await db.clients.find(
                {"status": "ACTIVE"},
                {"_id": 0}
            ).to_list(1000)
            
            for client in clients:
                await self._generate_gst_tasks(client, now)
                await self._generate_itr_tasks(client, now)
                await self._generate_tds_tasks(client, now)
            
            logger.info("Recurring tasks generated successfully")
        except Exception as e:
            logger.error(f"Error generating recurring tasks: {str(e)}")
    
    async def _generate_gst_tasks(self, client: Dict, now: datetime):
        """Generate GST filing tasks."""
        # Check if client has GSTIN
        if not client.get('gstin'):
            return
        
        # GST monthly return - GSTR-3B due on 20th of next month
        next_month = now.replace(day=1) + timedelta(days=32)
        due_date = next_month.replace(day=20, hour=23, minute=59)
        
        # Check if task already exists
        existing = await db.tasks.find_one({
            "client_id": client['id'],
            "task_type": "GST",
            "title": {"$regex": f"GSTR-3B.*{next_month.strftime('%B %Y')}"}
        })
        
        if not existing:
            task = {
                "id": str(uuid.uuid4()),
                "title": f"GSTR-3B Filing - {next_month.strftime('%B %Y')}",
                "description": "Monthly GST return filing",
                "client_id": client['id'],
                "client_name": client['name'],
                "task_type": "GST",
                "due_date": due_date.isoformat(),
                "status": "PENDING",
                "priority": "HIGH",
                "assigned_to": None,
                "created_at": now.isoformat(),
                "auto_generated": True
            }
            await db.tasks.insert_one(task)
            logger.info(f"Generated GST task for client {client['name']}")
    
    async def _generate_itr_tasks(self, client: Dict, now: datetime):
        """Generate ITR filing tasks."""
        # Check if client has PAN
        if not client.get('pan'):
            return
        
        # ITR deadline - July 31st of each year (for previous FY)
        if now.month <= 7:
            # Current year deadline
            due_date = datetime(now.year, 7, 31, 23, 59, tzinfo=timezone.utc)
            fy = f"{now.year-1}-{str(now.year)[2:]}"
        else:
            # Next year deadline
            due_date = datetime(now.year + 1, 7, 31, 23, 59, tzinfo=timezone.utc)
            fy = f"{now.year}-{str(now.year + 1)[2:]}"
        
        # Only generate if we're within 3 months of deadline
        if (due_date - now).days <= 90 and (due_date - now).days > 0:
            existing = await db.tasks.find_one({
                "client_id": client['id'],
                "task_type": "ITR",
                "title": {"$regex": f"ITR Filing.*FY {fy}"}
            })
            
            if not existing:
                task = {
                    "id": str(uuid.uuid4()),
                    "title": f"ITR Filing - FY {fy}",
                    "description": "Annual Income Tax Return filing",
                    "client_id": client['id'],
                    "client_name": client['name'],
                    "task_type": "ITR",
                    "due_date": due_date.isoformat(),
                    "status": "PENDING",
                    "priority": "URGENT",
                    "assigned_to": None,
                    "created_at": now.isoformat(),
                    "auto_generated": True
                }
                await db.tasks.insert_one(task)
                logger.info(f"Generated ITR task for client {client['name']}")
    
    async def _generate_tds_tasks(self, client: Dict, now: datetime):
        """Generate TDS return filing tasks."""
        # Check if client has TAN (stored in additional fields)
        client_meta = await db.client_metadata.find_one({"client_id": client['id']})
        if not client_meta or not client_meta.get('tan'):
            return
        
        # TDS quarterly return - due on 31st of month after quarter end
        quarters = [
            (1, 3, 31, 7),   # Q4 of previous FY
            (4, 6, 31, 7),   # Q1
            (7, 9, 31, 10),  # Q2
            (10, 12, 31, 1)  # Q3
        ]
        
        for start_month, end_month, due_day, due_month_offset in quarters:
            quarter_end = datetime(now.year, end_month, 30, tzinfo=timezone.utc)
            due_month = end_month + due_month_offset
            due_year = now.year if due_month <= 12 else now.year + 1
            due_month = due_month if due_month <= 12 else due_month - 12
            
            due_date = datetime(due_year, due_month, due_day, 23, 59, tzinfo=timezone.utc)
            
            # Only generate if deadline is within next 30 days
            if 0 < (due_date - now).days <= 30:
                existing = await db.tasks.find_one({
                    "client_id": client['id'],
                    "task_type": "GENERAL",
                    "title": {"$regex": f"TDS Return.*Q{start_month//3 + 1}"}
                })
                
                if not existing:
                    task = {
                        "id": str(uuid.uuid4()),
                        "title": f"TDS Return Filing - Q{start_month//3 + 1}",
                        "description": "Quarterly TDS return",
                        "client_id": client['id'],
                        "client_name": client['name'],
                        "task_type": "GENERAL",
                        "due_date": due_date.isoformat(),
                        "status": "PENDING",
                        "priority": "HIGH",
                        "assigned_to": None,
                        "created_at": now.isoformat(),
                        "auto_generated": True
                    }
                    await db.tasks.insert_one(task)
                    logger.info(f"Generated TDS task for client {client['name']}")
    
    async def update_overdue_tasks(self):
        """Mark tasks as overdue if past due date."""
        try:
            now = datetime.now(timezone.utc)
            
            result = await db.tasks.update_many(
                {
                    "status": {"$in": ["PENDING", "IN_PROGRESS"]},
                    "due_date": {"$lt": now.isoformat()}
                },
                {"$set": {"status": "OVERDUE"}}
            )
            
            if result.modified_count > 0:
                logger.info(f"Marked {result.modified_count} tasks as overdue")
        except Exception as e:
            logger.error(f"Error updating overdue tasks: {str(e)}")
    
    async def auto_assign_tasks(self):
        """Auto-assign unassigned tasks to staff based on workload."""
        try:
            # Get all staff members
            staff = await db.staff.find({}, {"_id": 0}).to_list(100)
            if not staff:
                return
            
            # Get unassigned tasks
            unassigned_tasks = await db.tasks.find(
                {
                    "assigned_to": None,
                    "status": "PENDING"
                },
                {"_id": 0}
            ).to_list(100)
            
            if not unassigned_tasks:
                return
            
            # Calculate workload for each staff member
            workload = {}
            for member in staff:
                active_tasks = await db.tasks.count_documents({
                    "assigned_to": member['name'],
                    "status": {"$in": ["PENDING", "IN_PROGRESS"]}
                })
                workload[member['name']] = active_tasks
            
            # Assign tasks to staff with least workload
            for task in unassigned_tasks:
                # Find staff with minimum workload
                assignee = min(workload.keys(), key=lambda k: workload[k])
                
                # Update task
                await db.tasks.update_one(
                    {"id": task['id']},
                    {"$set": {"assigned_to": assignee}}
                )
                
                # Update workload
                workload[assignee] += 1
                
                logger.info(f"Auto-assigned task {task['id']} to {assignee}")
            
            logger.info(f"Auto-assigned {len(unassigned_tasks)} tasks")
        except Exception as e:
            logger.error(f"Error auto-assigning tasks: {str(e)}")
    
    def shutdown(self):
        """Shutdown scheduler gracefully."""
        self.scheduler.shutdown()
        logger.info("Automation scheduler stopped")

# Global automation service
automation_service = AutomationService()