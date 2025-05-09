import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { LocalizationProvider } from '@mui/x-date-pickers';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ConfigProvider, App as AntApp } from 'antd';
import Login from './components/Login';
import Layout from './components/Layout';
import Users from './components/users/Users';
import VMs from './components/VMs/VMs';
import Sales from './components/Sales/Sales';
import Partners from './components/Partners/Partners';
import Clients from './components/Clients/Clients';
import BidList from './components/Bids/BidList';
import BasicDetails from './components/Bids/BasicDetails';
import PartnerResponse from './components/Bids/PartnerResponse';
import InField from './components/Bids/InField';
import FieldAllocation from './components/Bids/FieldAllocation';
import Closure from './components/Bids/Closure';
import ClosureEdit from './components/Bids/ClosureEdit';
import ReadyForInvoiceBids from './components/Bids/ReadyForInvoiceBids';
import InvoiceEdit from './components/InvoiceEdit';
import Home from './components/Home';
import PartnerPublicForm from './components/PartnerPublicForm';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import PrivateRoute from './components/common/PrivateRoute';
import Unauthorized from './components/common/Unauthorized';
import PartnerResponseSuccess from './components/PartnerResponseSuccess';
import ProposalList from './components/Proposals/ProposalList';
import ProposalForm from './components/Proposals/ProposalForm';

// Protected Route component
const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  return isAuthenticated ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <ConfigProvider>
      <AntApp>
        <AuthProvider>
            <LocalizationProvider dateAdapter={AdapterDateFns}>
              <Routes>
                <Route path="/login" element={<Login />} />
              <Route path="/partner-response/:token" element={<PartnerPublicForm />} />
              <Route path="/partner-response/success" element={<PartnerResponseSuccess />} />
                <Route
                  path="/home"
                  element={
                    <ProtectedRoute>
                      <Home />
                    </ProtectedRoute>
                  }
                />
                <Route path="/" element={<Navigate to="/home" />} />
                
                <Route element={
                  <PrivateRoute>
                    <Layout />
                  </PrivateRoute>
                }>
                  <Route index element={<Home />} />
                  
                  <Route path="bids" element={
                    <PrivateRoute requiredPermissions={['can_view_bids']}>
                      <BidList />
                    </PrivateRoute>
                  } />
                  <Route path="bids/new" element={
                    <PrivateRoute requiredPermissions={['can_view_bids', 'can_edit_bids']}>
                      <BasicDetails />
                    </PrivateRoute>
                  } />
                  <Route path="bids/edit/:bidId" element={
                    <PrivateRoute requiredPermissions={['can_view_bids', 'can_edit_bids']}>
                      <BasicDetails />
                    </PrivateRoute>
                  } />
                  <Route path="bids/partner/:bidId" element={
                    <PrivateRoute requiredPermissions={['can_view_bids']}>
                      <PartnerResponse />
                    </PrivateRoute>
                  } />
                  <Route path="bids/field-allocation/:bidId" element={
                    <PrivateRoute requiredPermissions={['can_view_infield', 'can_edit_infield']}>
                      <FieldAllocation />
                    </PrivateRoute>
                  } />
                  
                  <Route path="infield" element={
                    <PrivateRoute requiredPermissions={['can_view_infield']}>
                      <InField />
                    </PrivateRoute>
                  } />
                  
                  <Route path="closure" element={
                    <PrivateRoute requiredPermissions={['can_view_closure']}>
                      <Closure />
                    </PrivateRoute>
                  } />
                  <Route path="closure/edit/:bidId" element={
                    <PrivateRoute requiredPermissions={['can_view_closure', 'can_edit_closure']}>
                      <ClosureEdit />
                    </PrivateRoute>
                  } />
                  
                  <Route path="invoice" element={
                    <PrivateRoute requiredPermissions={['can_view_invoice']}>
                      <ReadyForInvoiceBids />
                    </PrivateRoute>
                  } />
                  <Route path="invoice/:bidId/edit" element={
                    <PrivateRoute requiredPermissions={['can_view_invoice']}>
                      <InvoiceEdit />
                    </PrivateRoute>
                  } />
                  
                  <Route path="users" element={
                    <PrivateRoute requiredPermissions={['can_view_users']}>
                      <Users />
                    </PrivateRoute>
                  } />
                  <Route path="partners" element={
                    <PrivateRoute requiredPermissions={['can_view_users']}>
                      <Partners />
                    </PrivateRoute>
                  } />
                  <Route path="vms" element={
                    <PrivateRoute requiredPermissions={['can_view_users']}>
                      <VMs />
                    </PrivateRoute>
                  } />
                  <Route path="sales" element={
                    <PrivateRoute requiredPermissions={['can_view_users']}>
                      <Sales />
                    </PrivateRoute>
                  } />
                  <Route path="clients" element={
                    <PrivateRoute requiredPermissions={['can_view_users']}>
                      <Clients />
                    </PrivateRoute>
                  } />
                  
                  <Route path="accrual" element={
                    <PrivateRoute>
                      <div>Accrual Page</div>
                    </PrivateRoute>
                  } />
                  
                  <Route path="unauthorized" element={<Unauthorized />} />
                  <Route path="proposals" element={
                    <PrivateRoute>
                      <ProposalList />
                    </PrivateRoute>
                  } />
                  <Route path="proposals/new" element={
                    <PrivateRoute>
                      <ProposalForm />
                    </PrivateRoute>
                  } />
                  <Route path="proposals/:proposalId" element={
                    <PrivateRoute>
                      <ProposalForm />
                    </PrivateRoute>
                  } />
                </Route>
              </Routes>
            </LocalizationProvider>
        </AuthProvider>
      </AntApp>
    </ConfigProvider>
  );
}

export default App; 