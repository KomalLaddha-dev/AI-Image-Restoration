import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Navbar from './components/Navbar';
import Home from './pages/Home';
import RestorePage from './pages/RestorePage';
import IdentifyPage from './pages/IdentifyPage';
import HistoryDetail from './pages/HistoryDetail';

export default function App() {
  return (
    <BrowserRouter>
      <Navbar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/restore" element={<RestorePage />} />
        <Route path="/identify" element={<IdentifyPage />} />
        <Route path="/history/:id" element={<HistoryDetail />} />
      </Routes>
    </BrowserRouter>
  );
}
