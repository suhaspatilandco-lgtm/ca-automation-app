import React from 'react';
import '@/App.css';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import Clients from '@/pages/Clients';
import Tasks from '@/pages/Tasks';
import Documents from '@/pages/Documents';
import Invoices from '@/pages/Invoices';
import Staff from '@/pages/Staff';
import CAWorkflow from '@/pages/CAWorkflow';
import { Toaster } from 'sonner';

function App() {
  return (
    <div className="App">
      <Toaster position="top-right" richColors />
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="clients" element={<Clients />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="documents" element={<Documents />} />
            <Route path="invoices" element={<Invoices />} />
            <Route path="staff" element={<Staff />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </div>
  );
}

export default App;