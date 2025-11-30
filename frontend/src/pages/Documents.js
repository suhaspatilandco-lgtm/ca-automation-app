import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Plus, FileText, Download, Trash2, Filter } from 'lucide-react';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { format } from 'date-fns';
import { toast } from 'sonner';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

export const Documents = () => {
  const [documents, setDocuments] = useState([]);
  const [clients, setClients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [filterClient, setFilterClient] = useState('ALL');
  const [formData, setFormData] = useState({
    client_id: '',
    filename: '',
    file_url: '',
    category: 'General'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [docsRes, clientsRes] = await Promise.all([
        axios.get(`${API}/documents`),
        axios.get(`${API}/clients`)
      ]);
      setDocuments(docsRes.data);
      setClients(clientsRes.data);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast.error('Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // In a real app, you would upload the file to cloud storage first
      // For demo purposes, we're using a placeholder URL
      const docData = {
        ...formData,
        file_url: formData.file_url || `https://example.com/docs/${formData.filename}`
      };
      await axios.post(`${API}/documents`, docData);
      toast.success('Document uploaded successfully');
      fetchData();
      handleCloseDialog();
    } catch (error) {
      console.error('Error uploading document:', error);
      toast.error('Failed to upload document');
    }
  };

  const handleDelete = async (docId) => {
    if (!window.confirm('Are you sure you want to delete this document?')) return;
    try {
      await axios.delete(`${API}/documents/${docId}`);
      toast.success('Document deleted successfully');
      fetchData();
    } catch (error) {
      console.error('Error deleting document:', error);
      toast.error('Failed to delete document');
    }
  };

  const handleCloseDialog = () => {
    setDialogOpen(false);
    setFormData({
      client_id: '',
      filename: '',
      file_url: '',
      category: 'General'
    });
  };

  const filteredDocuments = documents.filter(doc => 
    filterClient === 'ALL' || doc.client_id === filterClient
  );

  const getCategoryColor = (category) => {
    const colors = {
      'GST': 'bg-emerald-100 text-emerald-700',
      'ITR': 'bg-blue-100 text-blue-700',
      'Audit': 'bg-purple-100 text-purple-700',
      'ROC': 'bg-amber-100 text-amber-700',
      'Financial': 'bg-pink-100 text-pink-700',
      'Legal': 'bg-red-100 text-red-700',
      'General': 'bg-slate-100 text-slate-700'
    };
    return colors[category] || colors['General'];
  };

  return (
    <div className="space-y-6 page-enter" data-testid="documents-page">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
        <Select value={filterClient} onValueChange={setFilterClient}>
          <SelectTrigger className="w-[200px]" data-testid="filter-client-select">
            <Filter size={16} className="mr-2" />
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="ALL">All Clients</SelectItem>
            {clients.map(client => (
              <SelectItem key={client.id} value={client.id}>{client.name}</SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button className="bg-emerald-600 hover:bg-emerald-700" data-testid="add-document-btn">
              <Plus size={20} className="mr-2" />
              Upload Document
            </Button>
          </DialogTrigger>
          <DialogContent className="max-w-xl" data-testid="document-dialog">
            <DialogHeader>
              <DialogTitle>Upload Document</DialogTitle>
            </DialogHeader>
            <form onSubmit={handleSubmit} className="space-y-4" data-testid="document-form">
              <div>
                <Label htmlFor="client">Client *</Label>
                <Select value={formData.client_id} onValueChange={(value) => setFormData({ ...formData, client_id: value })} required>
                  <SelectTrigger data-testid="document-client-select">
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
                <Label htmlFor="filename">File Name *</Label>
                <Input
                  id="filename"
                  value={formData.filename}
                  onChange={(e) => setFormData({ ...formData, filename: e.target.value })}
                  placeholder="e.g., Annual_Report_2024.pdf"
                  required
                  data-testid="document-filename-input"
                />
              </div>
              <div>
                <Label htmlFor="category">Category *</Label>
                <Select value={formData.category} onValueChange={(value) => setFormData({ ...formData, category: value })}>
                  <SelectTrigger data-testid="document-category-select">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="GST">GST</SelectItem>
                    <SelectItem value="ITR">ITR</SelectItem>
                    <SelectItem value="Audit">Audit</SelectItem>
                    <SelectItem value="ROC">ROC</SelectItem>
                    <SelectItem value="Financial">Financial</SelectItem>
                    <SelectItem value="Legal">Legal</SelectItem>
                    <SelectItem value="General">General</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <Label htmlFor="file_url">File URL (Optional)</Label>
                <Input
                  id="file_url"
                  value={formData.file_url}
                  onChange={(e) => setFormData({ ...formData, file_url: e.target.value })}
                  placeholder="https://..."
                  data-testid="document-url-input"
                />
                <p className="text-xs text-slate-500 mt-1">In production, file upload would be integrated here</p>
              </div>
              <div className="flex justify-end gap-3 pt-4">
                <Button type="button" variant="outline" onClick={handleCloseDialog} data-testid="cancel-btn">
                  Cancel
                </Button>
                <Button type="submit" className="bg-emerald-600 hover:bg-emerald-700" data-testid="submit-document-btn">
                  Upload
                </Button>
              </div>
            </form>
          </DialogContent>
        </Dialog>
      </div>

      {/* Documents Grid */}
      {loading ? (
        <div className="flex items-center justify-center h-64" data-testid="loading-documents">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-500"></div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6" data-testid="documents-grid">
          {filteredDocuments.map((doc) => (
            <div
              key={doc.id}
              className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 hover:shadow-md transition-all duration-200 card-hover"
              data-testid={`document-card-${doc.id}`}
            >
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 bg-slate-100 rounded-lg">
                    <FileText className="text-slate-600" size={24} />
                  </div>
                  <div className="flex-1">
                    <h3 className="font-semibold text-slate-900 text-sm mb-1" data-testid={`document-name-${doc.id}`}>
                      {doc.filename}
                    </h3>
                    <span className={`status-badge text-xs ${getCategoryColor(doc.category)}`}>
                      {doc.category}
                    </span>
                  </div>
                </div>
              </div>
              <div className="space-y-2 text-sm mb-4">
                {doc.client_name && (
                  <p className="text-slate-600">
                    Client: <span className="font-medium">{doc.client_name}</span>
                  </p>
                )}
                <p className="text-slate-500 text-xs mono">
                  Uploaded: {format(new Date(doc.uploaded_at), 'MMM dd, yyyy')}
                </p>
              </div>
              <div className="flex gap-2">
                <Button
                  size="sm"
                  variant="outline"
                  className="flex-1"
                  onClick={() => window.open(doc.file_url, '_blank')}
                  data-testid={`download-document-${doc.id}`}
                >
                  <Download size={16} className="mr-2" />
                  Download
                </Button>
                <Button
                  size="sm"
                  variant="outline"
                  className="text-red-600 hover:bg-red-50 hover:text-red-700"
                  onClick={() => handleDelete(doc.id)}
                  data-testid={`delete-document-${doc.id}`}
                >
                  <Trash2 size={16} />
                </Button>
              </div>
            </div>
          ))}
        </div>
      )}

      {!loading && filteredDocuments.length === 0 && (
        <div className="text-center py-12" data-testid="no-documents">
          <FileText className="mx-auto text-slate-300 mb-3" size={48} />
          <p className="text-slate-500">No documents found</p>
        </div>
      )}
    </div>
  );
};

export default Documents;