import React, { useState, useEffect } from 'react';
import { Activity, Wifi, Video, Camera, Clock, FileText, Eye, RefreshCw } from 'lucide-react';
import { io } from "socket.io-client";

// REPLACE WITH YOUR IP IF NEEDED (e.g., 'http://192.168.100.8:5000')
const API_BASE = 'http://192.168.100.8:5000';

export default function Dashboard() {
  const [stats, setStats] = useState({ camera: false, mqtt: false, recording: false });
  const [logs, setLogs] = useState([]);
  const [events, setEvents] = useState([]); // Stores the DB table data
  const [loading, setLoading] = useState(false);

  // --- 1. Fetch Data Logic ---
  const fetchData = () => {
    // Fetch System Health
    fetch(`${API_BASE}/api/health`)
      .then(res => res.json())
      .then(data => setStats(data))
      .catch(console.error);
    
    // Fetch DB Events for Table
    setLoading(true);
    fetch(`${API_BASE}/api/events`)
        .then(res => res.json())
        .then(data => {
            if(Array.isArray(data)) setEvents(data);
            setLoading(false);
        })
        .catch(e => { console.error(e); setLoading(false); });
  };

  useEffect(() => {
    const socket = io(API_BASE);
    
    // Listen for real-time updates
    socket.on('device_update', () => fetchData());
    socket.on('new_log', (log) => setLogs(prev => [log, ...prev].slice(0, 20)));
    socket.on('new_event', () => {
        // When AI detects something, refresh the table automatically
        fetchData();
    });

    fetchData(); // Initial load
    const interval = setInterval(fetchData, 5000); // Poll every 5s as backup
    return () => { socket.disconnect(); clearInterval(interval); };
  }, []);

  // --- 2. Helper Components ---
  const Card = ({ title, status, icon: Icon, color }) => (
    <div className="bg-slate-800 border border-slate-700 p-6 rounded-2xl relative overflow-hidden transition-all hover:border-slate-600">
      <div className={`absolute top-0 right-0 p-4 opacity-10 ${status ? `text-${color}-500` : 'text-slate-500'}`}><Icon size={80} /></div>
      <h3 className="text-slate-400 text-sm font-bold uppercase tracking-wider">{title}</h3>
      <div className="flex items-center gap-3 mt-2">
        <div className={`w-3 h-3 rounded-full ${status ? `bg-${color}-500 shadow-[0_0_10px]` : 'bg-slate-600'}`}></div>
        <span className="text-2xl font-bold text-white">{status ? 'ONLINE' : 'OFFLINE'}</span>
      </div>
    </div>
  );

  return (
    <div className="max-w-7xl mx-auto space-y-8 pb-10">
      
      {/* HEADER */}
      <div className="flex justify-between items-end">
        <div>
            <h2 className="text-3xl font-bold text-white">System Overview</h2>
            <p className="text-slate-400 mt-1">Real-time monitoring & detection logs</p>
        </div>
        <button onClick={fetchData} className="p-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg border border-slate-700 transition-colors">
            <RefreshCw size={20} className={loading ? "animate-spin" : ""} />
        </button>
      </div>
      
      {/* 1. TOP STATS */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card title="Camera Feed" status={stats.camera} icon={Camera} color="green" />
        <Card title="MQTT Link" status={stats.mqtt} icon={Wifi} color="blue" />
        <Card title="Recording" status={stats.recording} icon={Video} color="red" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* 2. DETECTION HISTORY TABLE (Takes up 2/3 space) */}
        <div className="lg:col-span-2 bg-slate-800/50 border border-slate-700 rounded-2xl overflow-hidden flex flex-col h-[500px]">
            <div className="p-5 border-b border-slate-700 bg-slate-800 flex justify-between items-center">
                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                    <FileText className="text-blue-400" size={20}/> Detection History
                </h3>
                <span className="text-xs bg-blue-900/30 text-blue-300 px-2 py-1 rounded border border-blue-900/50">
                    Latest {events.length}
                </span>
            </div>
            
            <div className="overflow-auto flex-1 p-0">
                <table className="w-full text-left border-collapse">
                    <thead className="bg-slate-900/50 text-slate-400 text-xs uppercase sticky top-0 backdrop-blur-md">
                        <tr>
                            <th className="p-4 font-semibold">Time</th>
                            <th className="p-4 font-semibold">AI Analysis</th>
                            <th className="p-4 font-semibold text-right">Proof</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-700/50 text-sm">
                        {events.length === 0 ? (
                            <tr><td colSpan="3" className="p-8 text-center text-slate-500">No detections recorded yet.</td></tr>
                        ) : (
                            events.map((ev) => (
                                <tr key={ev.id} className="hover:bg-slate-700/30 transition-colors group">
                                    <td className="p-4 text-slate-300 font-mono whitespace-nowrap">
                                        <div className="flex items-center gap-2">
                                            <Clock size={14} className="text-slate-500"/> {ev.timestamp}
                                        </div>
                                    </td>
                                    <td className="p-4 text-slate-200">
                                        {ev.analysis.includes("API_ERROR") ? (
                                            <span className="text-red-400 flex items-center gap-1"><Activity size={14}/> Analysis Failed</span>
                                        ) : (
                                            ev.analysis
                                        )}
                                    </td>
                                    <td className="p-4 text-right">
                                        <a href={ev.image_url} target="_blank" rel="noopener noreferrer" 
                                           className="inline-flex items-center gap-1 px-3 py-1.5 bg-slate-700 hover:bg-blue-600 text-white text-xs rounded-lg transition-all group-hover:shadow-lg">
                                            <Eye size={14} /> View
                                        </a>
                                    </td>
                                </tr>
                            ))
                        )}
                    </tbody>
                </table>
            </div>
        </div>

        {/* 3. SYSTEM LOGS (Side Panel) */}
        <div className="bg-slate-800/50 border border-slate-700 rounded-2xl p-6 h-[500px] flex flex-col">
          <h3 className="text-lg font-bold text-white mb-4 flex items-center gap-2">
            <Activity className="text-emerald-400" size={20} /> System Logs
          </h3>
          <div className="space-y-2 overflow-y-auto flex-1 pr-2 custom-scrollbar">
            {logs.length === 0 && <p className="text-slate-500 text-center mt-10">System is quiet...</p>}
            {logs.map((log, i) => (
              <div key={i} className="flex gap-3 p-3 bg-slate-800 rounded-lg border border-slate-700/50 hover:border-slate-600 transition-colors">
                <span className="text-[10px] font-mono text-slate-500 mt-0.5">{log.time}</span>
                <span className="text-xs text-slate-300 leading-relaxed">{log.event}</span>
              </div>
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}