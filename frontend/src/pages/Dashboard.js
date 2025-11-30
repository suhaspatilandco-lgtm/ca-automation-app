import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Users, CheckSquare, Receipt, TrendingUp, Calendar, AlertCircle } from 'lucide-react';
import { format } from 'date-fns';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Dashboard = () => {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchDashboardStats();
  }, []);

  const fetchDashboardStats = async () => {
    try {
      const response = await axios.get(`${API}/dashboard/stats`);
      setStats(response.data);
    } catch (error) {
      console.error('Error fetching dashboard stats:', error);
      toast.error('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const statCards = [
    {
      title: 'Total Clients',
      value: stats?.total_clients || 0,
      icon: Users,
      color: 'emerald',
      bgColor: 'bg-emerald-50',
      iconColor: 'text-emerald-600',
      testId: 'stat-total-clients'
    },
    {
      title: 'Active Tasks',
      value: stats?.active_tasks || 0,
      icon: CheckSquare,
      color: 'amber',
      bgColor: 'bg-amber-50',
      iconColor: 'text-amber-600',
      testId: 'stat-active-tasks'
    },
    {
      title: 'Pending Invoices',
      value: stats?.pending_invoices || 0,
      icon: Receipt,
      color: 'blue',
      bgColor: 'bg-blue-50',
      iconColor: 'text-blue-600',
      testId: 'stat-pending-invoices'
    },
    {
      title: 'Total Revenue',
      value: `₹${(stats?.total_revenue || 0).toLocaleString()}`,
      icon: TrendingUp,
      color: 'purple',
      bgColor: 'bg-purple-50',
      iconColor: 'text-purple-600',
      testId: 'stat-total-revenue'
    }
  ];

  const getPriorityColor = (priority) => {
    switch (priority) {
      case 'URGENT': return 'text-red-600 bg-red-50';
      case 'HIGH': return 'text-orange-600 bg-orange-50';
      case 'MEDIUM': return 'text-amber-600 bg-amber-50';
      case 'LOW': return 'text-blue-600 bg-blue-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getTaskTypeColor = (type) => {
    switch (type) {
      case 'GST': return 'text-emerald-700 bg-emerald-100';
      case 'ITR': return 'text-blue-700 bg-blue-100';
      case 'AUDIT': return 'text-purple-700 bg-purple-100';
      case 'ROC': return 'text-amber-700 bg-amber-100';
      default: return 'text-gray-700 bg-gray-100';
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64" data-testid="loading-dashboard">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
      </div>
    );
  }

  return (
    <div className="space-y-8 page-enter" data-testid="dashboard-page">
      {/* Welcome Section */}
      <div className="bg-gradient-to-br from-slate-900 to-slate-800 rounded-xl p-8 text-white shadow-lg">
        <h1 className="text-4xl font-bold mb-2" data-testid="welcome-heading">Welcome Back!</h1>
        <p className="text-slate-300 text-lg">Here's what's happening with your practice today</p>
      </div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map((stat) => {
          const Icon = stat.icon;
          return (
            <div
              key={stat.title}
              className="bg-white rounded-lg p-6 shadow-sm hover:shadow-md transition-all duration-200 border border-slate-200 card-hover"
              data-testid={stat.testId}
            >
              <div className="flex items-center justify-between mb-4">
                <div className={`${stat.bgColor} p-3 rounded-lg`}>
                  <Icon className={stat.iconColor} size={24} />
                </div>
              </div>
              <p className="text-sm text-slate-600 mb-1">{stat.title}</p>
              <p className="text-3xl font-bold text-slate-900 mono" data-testid={`${stat.testId}-value`}>
                {stat.value}
              </p>
            </div>
          );
        })}
      </div>

      {/* Upcoming Deadlines */}
      <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
        <div className="bg-slate-50 px-6 py-4 border-b border-slate-200">
          <div className="flex items-center gap-2">
            <Calendar className="text-slate-600" size={20} />
            <h2 className="text-xl font-semibold text-slate-900" data-testid="upcoming-deadlines-heading">
              Upcoming Deadlines
            </h2>
          </div>
        </div>
        <div className="divide-y divide-slate-100" data-testid="deadlines-list">
          {stats?.upcoming_deadlines && stats.upcoming_deadlines.length > 0 ? (
            stats.upcoming_deadlines.map((task, index) => (
              <div
                key={task.id}
                className="p-6 hover:bg-slate-50 transition-colors duration-150"
                data-testid={`deadline-item-${index}`}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <h3 className="font-semibold text-slate-900" data-testid={`task-title-${index}`}>
                        {task.title}
                      </h3>
                      <span className={`text-xs px-2 py-1 rounded ${getTaskTypeColor(task.task_type)}`}>
                        {task.task_type}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded ${getPriorityColor(task.priority)}`}>
                        {task.priority}
                      </span>
                    </div>
                    {task.client_name && (
                      <p className="text-sm text-slate-600 mb-1">
                        Client: <span className="font-medium">{task.client_name}</span>
                      </p>
                    )}
                    {task.description && (
                      <p className="text-sm text-slate-500">{task.description}</p>
                    )}
                  </div>
                  <div className="text-right ml-4">
                    <div className="flex items-center gap-1 text-amber-600">
                      <AlertCircle size={16} />
                      <p className="text-sm font-medium mono" data-testid={`task-due-date-${index}`}>
                        {format(new Date(task.due_date), 'MMM dd, yyyy')}
                      </p>
                    </div>
                  </div>
                </div>
              </div>
            ))
          ) : (
            <div className="p-12 text-center" data-testid="no-deadlines">
              <Calendar className="mx-auto text-slate-300 mb-3" size={48} />
              <p className="text-slate-500">No upcoming deadlines</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Dashboard;