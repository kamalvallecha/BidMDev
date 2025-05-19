import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Home from './components/Home';
import Partners from './components/Partners/Partners';
import PartnerPublicForm from './components/PartnerPublicForm';
import ProposalList from './components/Proposals/ProposalList';
import ProposalForm from './components/Proposals/ProposalForm';
import './App.css';

function App() {
    return (
        <Routes>
            <Route path="/" element={<Layout />}>
                <Route index element={<Home />} />
                <Route path="partner-response/:token" element={<PartnerPublicForm />} />
                <Route path="bids" element={<div>Bids Page</div>} />
                <Route path="infield" element={<div>InField Page</div>} />
                <Route path="closure" element={<div>Closure Page</div>} />
                <Route path="ready-for-invoice" element={<div>Ready for Invoice Page</div>} />
                <Route path="accrual" element={<div>Accrual Page</div>} />
                <Route path="all-users" element={<div>All Users Page</div>} />
                <Route path="partners" element={<Partners />} />
                <Route path="proposals" element={<ProposalList />} />
                <Route path="proposals/new" element={<ProposalForm />} />
                <Route path="proposals/:proposalId" element={<ProposalForm />} />
                <Route path="*" element={<div>404 Not Found</div>} />
            </Route>
        </Routes>
    );
}

export default App; 