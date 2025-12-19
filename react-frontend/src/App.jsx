import React, { useState } from "react";
import { BrowserRouter as Router, Routes, Route, Link, useLocation } from "react-router-dom";
import { LayoutDashboard, Cctv, Menu, X } from "lucide-react";
import Dashboard from "./pages/Dashboard";
import CameraPage from "./pages/CameraPage";

// Sidebar Link Component (Updated to close menu on click)
const NavItem = ({ to, icon: Icon, label, onClick }) => {
  const location = useLocation();
  const isActive = location.pathname === to;
  return (
    <Link 
      to={to} 
      onClick={onClick}
      className={`flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${isActive ? "bg-blue-600 text-white shadow-lg shadow-blue-900/50" : "text-slate-400 hover:bg-slate-800 hover:text-white"}`}
    >
      <Icon size={20} />
      <span className="font-medium">{label}</span>
    </Link>
  );
};

export default function App() {
  const [isSidebarOpen, setSidebarOpen] = useState(false);

  return (
    <Router>
      <div className="flex h-screen bg-slate-900 text-slate-200 overflow-hidden">
        
        {/* MOBILE OVERLAY (Click background to close) */}
        {isSidebarOpen && (
          <div 
            className="fixed inset-0 bg-black/60 z-40 md:hidden backdrop-blur-sm"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* SIDEBAR */}
        <div className={`
            fixed inset-y-0 left-0 z-50 w-64 bg-slate-950 border-r border-slate-800 flex flex-col p-4 
            transition-transform duration-300 ease-in-out
            ${isSidebarOpen ? "translate-x-0" : "-translate-x-full"} 
            md:relative md:translate-x-0
        `}>
          <div className="mb-8 px-4 flex items-center justify-between">
            <div className="flex items-center gap-2">
                <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                    <Cctv className="text-white" size={20} />
                </div>
                <h3 className="text-xl font-bold tracking-tight">Smart<span className="text-blue-500">Cam</span></h3>
            </div>
            {/* Close Button (Mobile Only) */}
            <button 
                onClick={() => setSidebarOpen(false)} 
                className="md:hidden text-slate-400 hover:text-white bg-slate-800 p-1 rounded-lg"
            >
              <X size={20} />
            </button>
          </div>

          <nav className="space-y-2 flex-1">
            <NavItem 
                to="/" 
                icon={LayoutDashboard} 
                label="Dashboard" 
                onClick={() => setSidebarOpen(false)} 
            />
            <NavItem 
                to="/camera" 
                icon={Cctv} 
                label="Live Camera" 
                onClick={() => setSidebarOpen(false)} 
            />
          </nav>
          
          <div className="mt-auto px-4 py-4 text-xs text-slate-600 text-center">
            v1.0.0 Mobile Ready
          </div>
        </div>

        {/* MAIN CONTENT WRAPPER */}
        <div className="flex-1 flex flex-col h-full w-full relative">
            
            {/* MOBILE HEADER (Hamburger Menu) */}
            <div className="md:hidden h-16 bg-slate-950 border-b border-slate-800 flex items-center px-4 justify-between shrink-0 sticky top-0 z-30">
                <div className="flex items-center gap-2">
                    <div className="w-8 h-8 bg-blue-600 rounded-lg flex items-center justify-center">
                        <Cctv className="text-white" size={20} />
                    </div>
                    <span className="font-bold text-lg text-white">SmartCam</span>
                </div>
                <button 
                    onClick={() => setSidebarOpen(true)} 
                    className="p-2 text-slate-200 hover:bg-slate-800 rounded-lg transition-colors"
                >
                    <Menu size={28} />
                </button>
            </div>

            {/* SCROLLABLE PAGE AREA */}
            <div className="flex-1 overflow-x-hidden overflow-y-auto bg-slate-900">
                <Routes>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/camera" element={<CameraPage />} />
                </Routes>
            </div>
        </div>

      </div>
    </Router>
  );
}