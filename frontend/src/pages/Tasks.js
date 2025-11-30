import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Filter, Calendar as CalendarIcon } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Textarea } from '@/components/ui/textarea';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { format } from 'date-fns';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Tasks = () => {
  const [tasks, setTasks] = useState([]);
  const [clients, setClients] = useState([]);
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [filterType, setFilterType] = useState('ALL');
  const [filterStatus, setFilterStatus] = useState('ALL');
  const [formData, setFormData] = useState({
    title: '',
    description: '',
    client_id: '',
    task_type: 'GENERAL',
    due_date: new Date(),
    status: 'PENDING',
    priority: 'MEDIUM',
    assigned_to: ''
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [tasksRes, clientsRes, staffRes] = await Promise.all([
        axios.get(`${API}/tasks`),
        axios.get(`${API}/clients`),
        axios.get(`${API}/staff`)
      ]);
      setTasks(tasksRes.data);
      setClients(clientsRes.data);
      setStaff(staffRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load tasks');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/tasks`, formData);
      toast.success('Task created successfully');
      fetchData();
      handleCloseDialog();
    } catch (error) {
      console.error('Error creating task:', error);
      toast.error('Failed to create task');
    }
  };

  const handleUpdateStatus = async (taskId, newStatus) => {
    try {
      const task = tasks.find(t => t.id === taskId);
      await axios.put(`${API}/tasks/${taskId}`, {
        ...task,
        status: newStatus,
        due_date: new Date(task.due_date)
      });
      toast.success('Task status updated');
      fetchData();
    } catch (error) {
      console.error('Error updating task:', error);
      toast.error('Failed to update task');
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setFormData({
      title: '',
      description: '',
      client_id: '',
      task_type: 'GENERAL',
      due_date: new Date(),
      status: 'PENDING',
      priority: 'MEDIUM',
      assigned_to: ''
    });
  };

  const filteredTasks = tasks.filter(task => {
    const typeMatch = filterType === 'ALL' || task.task_type === filterType;
    const statusMatch = filterStatus === 'ALL' || task.status === filterStatus;
    return typeMatch && statusMatch;
  });

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'URGENT': return 'priority-urgent';
      case 'HIGH': return 'priority-high';
      case 'MEDIUM': return 'priority-medium';
      case 'LOW': return 'priority-low';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED': return 'status-completed';
      case 'IN_PROGRESS': return 'bg-blue-100 text-blue-700';
      case 'PENDING': return 'status-pending';
      case 'OVERDUE': return 'status-overdue';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  const getTaskTypeColor = (type) => {
    switch (type) {
      case 'GST': return 'bg-emerald-100 text-emerald-700';
      case 'ITR': return 'bg-blue-100 text-blue-700';
      case 'AUDIT': return 'bg-purple-100 text-purple-700';
      case 'ROC': return 'bg-amber-100 text-amber-700';
      default: return 'bg-gray-100 text-gray-700';
    }
  };

  return (
    <div className="space-y-6 page-enter" data-testid="tasks-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <div className="flex gap-3">
          <Select value={filterType} onValueChange={setFilterType}>
            <SelectTrigger className="w-[150px]" data-testid="filter-type-select">
              <Filter size={16} className="mr-2" />
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Types</SelectItem>
              <SelectItem value="GST">GST</SelectItem>
              <SelectItem value="ITR">ITR</SelectItem>
              <SelectItem value="AUDIT">Audit</SelectItem>
              <SelectItem value="ROC">ROC</SelectItem>
              <SelectItem value="GENERAL">General</SelectItem>
            </SelectContent>
          </Select>
          <Select value={filterStatus} onValueChange={setFilterStatus}>
            <SelectTrigger className="w-[150px]" data-testid="filter-status-select">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Status</SelectItem>
              <SelectItem value="PENDING">Pending</SelectItem>
              <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
              <SelectItem value="COMPLETED">Completed</SelectItem>
              <SelectItem value="OVERDUE">Overdue</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-task-btn">
              <Plus size={20} className="mr-2" />
              Add Task
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto" data-testid="task-dialog">
            <DialogHeader>
              <DialogTitle>Add New Task</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="task-form">
              <div>
                <Label htmlFor="title">Task Title *</Label>
                <Input
                  id="title"
                  value={formData.title}
                  onChange={(e) => setFormData({ ...formData, title: e.target.value })}
                  required
                  data-testid="task-title-input"
                />
              </div>
              <div>
                <Label htmlFor="description">Description</Label>
                <Textarea
                  id="description"
                  value={formData.description}
                  onChange={(e) => setFormData({ ...formData, description: e.target.value })}
                  rows={3}
                  data-testid="task-description-input"
                />
              </div>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <Label htmlFor="client">Client *</Label>
                  <Select value={formData.client_id} onValueChange={(value) => setFormData({ ...formData, client_id: value })} required>
                    <SelectTrigger data-testid="task-client-select">
                      <SelectValue placeholder="Select client" />
                    </SelectTrigger>
                    <SelectContent>
                      {clients.map(client => (
                        <SelectItem key={client.id} value={client.id}>{client.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="task_type">Task Type *</Label>
                  <Select value={formData.task_type} onValueChange={(value) => setFormData({ ...formData, task_type: value })}>
                    <SelectTrigger data-testid="task-type-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="GST">GST</SelectItem>
                      <SelectItem value="ITR">ITR</SelectItem>
                      <SelectItem value="AUDIT">Audit</SelectItem>
                      <SelectItem value="ROC">ROC</SelectItem>
                      <SelectItem value="GENERAL">General</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label htmlFor="priority">Priority</Label>
                  <Select value={formData.priority} onValueChange={(value) => setFormData({ ...formData, priority: value })}>
                    <SelectTrigger data-testid="task-priority-select">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="LOW">Low</SelectItem>
                      <SelectItem value="MEDIUM">Medium</SelectItem>
                      <SelectItem value="HIGH">High</SelectItem>
                      <SelectItem value="URGENT">Urgent</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div>
                  <Label>Due Date *</Label>
                  <Popover>
                    <PopoverTrigger asChild>
                      <Button
                        variant="outline"
                        className="w-full justify-start text-left font-normal"
                        data-testid="task-due-date-btn"
                      >
                        <CalendarIcon className="mr-2 h-4 w-4" />
                        {formData.due_date ? format(formData.due_date, 'PPP') : <span>Pick a date</span>}
                      </Button>
                    </PopoverTrigger>
                    <PopoverContent className="w-auto p-0">
                      <Calendar
                        mode="single"
                        selected={formData.due_date}
                        onSelect={(date) => setFormData({ ...formData, due_date: date })}
                        initialFocus
                      />
                    </PopoverContent>
                  </Popover>
                </div>
                <div>
                  <Label htmlFor="assigned_to">Assign To</Label>
                  <Select value={formData.assigned_to} onValueChange={(value) => setFormData({ ...formData, assigned_to: value })}>
                    <SelectTrigger data-testid="task-assign-select">
                      <SelectValue placeholder="Select staff" />
                    </SelectTrigger>
                    <SelectContent>
                      {staff.map(member => (
                        <SelectItem key={member.id} value={member.name}>{member.name}</SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={handleCloseDialog} data-testid="cancel-btn">
                  Cancel
                </Button>
                <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700" data-testid="submit-task-btn">
                  Create Task
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Tasks List */}
      {loading ? (
        <div className="flex items-center justify-center h-64" data-testid="loading-tasks">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
        </div>
      ) : (
        <div className="space-y-4" data-testid="tasks-list">
          {filteredTasks.map((task) => (
            <div
              key={task.id}
              className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 hover:shadow-md transition-all duration-200"
              data-testid={`task-card-${task.id}`}
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-lg font-semibold text-slate-900" data-testid={`task-title-${task.id}`}>
                      {task.title}
                    </h3>
                    <span className={`status-badge ${getTaskTypeColor(task.task_type)}`}>
                      {task.task_type}
                    </span>
                    <span className={`status-badge ${getPriorityColor(task.priority)}`}>
                      {task.priority}
                    </span>
                  </div>
                  {task.client_name && (
                    <p className="text-sm text-slate-600 mb-2">
                      Client: <span className="font-medium">{task.client_name}</span>
                    </p>
                  )}
                  {task.description && (
                    <p className="text-sm text-slate-500 mb-3">{task.description}</p>
                  )}
                  <div className="flex items-center gap-4 text-sm text-slate-600">
                    <div className="flex items-center gap-1">
                      <CalendarIcon size={16} />
                      <span className="mono">{format(new Date(task.due_date), 'MMM dd, yyyy')}</span>
                    </div>
                    {task.assigned_to && (
                      <span>Assigned to: <span className="font-medium">{task.assigned_to}</span></span>
                    )}
                  </div>
                </div>
                <div>
                  <Select value={task.status} onValueChange={(value) => handleUpdateStatus(task.id, value)}>
                    <SelectTrigger className={`w-[150px] ${getStatusColor(task.status)}`} data-testid={`task-status-${task.id}`}>
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="PENDING">Pending</SelectItem>
                      <SelectItem value="IN_PROGRESS">In Progress</SelectItem>
                      <SelectItem value="COMPLETED">Completed</SelectItem>
                      <SelectItem value="OVERDUE">Overdue</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filteredTasks.length === 0 && (
        <div className="text-center py-12" data-testid="no-tasks">
          <p className="text-slate-500">No tasks found</p>
        </div>
      )}
    </div>
  );
};

export default Tasks;