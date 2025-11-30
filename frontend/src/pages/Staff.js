import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, Mail, Phone, Trash2, UserCog } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { format } from 'date-fns';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Staff = () => {
  const [staff, setStaff] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    role: '',
    phone: ''
  });

  useEffect(() => {
    fetchStaff();
  }, []);

  const fetchStaff = async () => {
    try {
      const response = await axios.get(`${API}/staff`);
      setStaff(response.data);
    } catch (error) {
      console.error('Error fetching staff:', error);
      toast.error('Failed to load staff');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await axios.post(`${API}/staff`, formData);
      toast.success('Staff member added successfully');
      fetchStaff();
      handleCloseDialog();
    } catch (error) {
      console.error('Error adding staff:', error);
      toast.error('Failed to add staff member');
    }
  };

  const handleDelete = async (staffId) => {
    if (!window.confirm('Are you sure you want to remove this staff member?')) return;
    try {
      await axios.delete(`${API}/staff/${staffId}`);
      toast.success('Staff member removed successfully');
      fetchStaff();
    } catch (error) {
      console.error('Error deleting staff:', error);
      toast.error('Failed to remove staff member');
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setFormData({
      name: '',
      email: '',
      role: '',
      phone: ''
    });
  };

  const getRoleColor = (role) => {
    const roleLower = role.toLowerCase();
    if (roleLower.includes('senior') || roleLower.includes('manager')) {
      return 'bg-purple-100 text-purple-700';
    } else if (roleLower.includes('associate') || roleLower.includes('junior')) {
      return 'bg-blue-100 text-blue-700';
    } else if (roleLower.includes('intern')) {
      return 'bg-amber-100 text-amber-700';
    }
    return 'bg-emerald-100 text-emerald-700';
  };

  return (
    <div className="space-y-6 page-enter" data-testid="staff-page">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-900">Team Members</h2>
          <p className="text-slate-600 mt-1">Manage your practice staff</p>
        </div>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-staff-btn">
              <Plus size={20} className="mr-2" />
              Add Staff
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl" data-testid="staff-dialog">
            <DialogHeader>
              <DialogTitle>Add New Staff Member</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="staff-form">
              <div>
                <Label htmlFor="name">Full Name *</Label>
                <Input
                  id="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  required
                  data-testid="staff-name-input"
                />
              </div>
              <div>
                <Label htmlFor="email">Email *</Label>
                <Input
                  id="email"
                  type="email"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  required
                  data-testid="staff-email-input"
                />
              </div>
              <div>
                <Label htmlFor="phone">Phone *</Label>
                <Input
                  id="phone"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  required
                  data-testid="staff-phone-input"
                />
              </div>
              <div>
                <Label htmlFor="role">Role *</Label>
                <Input
                  id="role"
                  value={formData.role}
                  onChange={(e) => setFormData({ ...formData, role: e.target.value })}
                  placeholder="e.g., Senior Associate, CA Intern"
                  required
                  data-testid="staff-role-input"
                />
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={handleCloseDialog} data-testid="cancel-btn">
                  Cancel
                </Button>
                <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700" data-testid="submit-staff-btn">
                  Add Staff Member
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Staff Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64" data-testid="loading-staff">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="staff-grid">
          {staff.map((member) => (
            <div
              key={member.id}
              className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 hover:shadow-md transition-all duration-200 card-hover"
              data-testid={`staff-card-${member.id}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-emerald-100 flex items-center justify-center">
                    <UserCog className="text-emerald-600" size={24} />
                  </div>
                  <div>
                    <h3 className="text-lg font-semibold text-slate-900" data-testid={`staff-name-${member.id}`}>
                      {member.name}
                    </h3>
                    <span className={`status-badge text-xs ${getRoleColor(member.role)}`}>
                      {member.role}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => handleDelete(member.id)}
                  className="p-2 text-slate-600 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                  data-testid={`delete-staff-${member.id}`}
                >
                  <Trash2 size={18} />
                </button>
              </div>
              <div className="space-y-2 text-sm">
                <div className="flex items-center gap-2 text-slate-600">
                  <Mail size={16} />
                  <span data-testid={`staff-email-${member.id}`}>{member.email}</span>
                </div>
                <div className="flex items-center gap-2 text-slate-600">
                  <Phone size={16} />
                  <span data-testid={`staff-phone-${member.id}`}>{member.phone}</span>
                </div>
                <p className="text-slate-500 text-xs pt-2">
                  Joined: {format(new Date(member.joined_date), 'MMM dd, yyyy')}
                </p>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && staff.length === 0 && (
        <div className="text-center py-12" data-testid="no-staff">
          <UserCog className="mx-auto text-slate-300 mb-3" size={48} />
          <p className="text-slate-500">No staff members added yet</p>
        </div>
      )}
    </div>
  );
};

export default Staff;