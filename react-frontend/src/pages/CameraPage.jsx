import React, { useState, useEffect } from "react";
import axios from "axios";
import { Settings, Power, Wifi, Video, Mic, ShieldCheck, Lightbulb, Camera, LightbulbOff } from "lucide-react";

const CameraPage = () => {
  // CONFIG: Change this to your backend IP
  const [serverIP, setServerIP] = useState("192.168.100.8");
  const API_BASE = `http://${serverIP}:5000`;

  const [logs, setLogs] = useState([]);
  const [camState, setCamState] = useState(true);
  const [systemHealth, setSystemHealth] = useState(null);
  
  // NEW: Track Light State (Default to false/off)
  const [lightOn, setLightOn] = useState(false);

  // --- FETCH DATA ---
  useEffect(() => {
    const fetchHealth = () => {
      axios.get(`${API_BASE}/api/health`)
        .then(res => setSystemHealth(res.data))
        .catch(console.error);
    };
    
    fetchHealth();
    const interval = setInterval(fetchHealth, 5000);
    return () => clearInterval(interval);
  }, [serverIP]);

  // --- ACTIONS ---
  const sendCommand = (action) => {
    axios.post(`${API_BASE}/api/control`, { action })
      .then(() => alert(`Sent: ${action}`))
      .catch(() => alert("Failed to send command"));
  };

  // UPDATED: Toggle Light Function
  const toggleLight = () => {
    const newState = !lightOn; // Calculate opposite of current state
    const endpoint = newState ? '/api/on' : '/api/off';
    
    axios.post(`${API_BASE}${endpoint}`)
      .then(res => {
          setLightOn(newState); // Update UI state only if successful
          // Optional: Show toast or alert
          // alert(`Light turned ${newState ? 'ON' : 'OFF'}`);
      })
      .catch(err => alert("Error: Check Python Backend Connection"));
  };

const handleCapture = () => {
    // Optional: Update button text to show loading state
    const btnText = document.getElementById("capture-text");
    if (btnText) btnText.innerText = "Saving...";

    // Make sure to use the lowercase endpoint '/api/capture'
    axios.post(`${API_BASE}/api/capture`)
      .then(res => {
        alert(res.data.message); // "Snapshot taken"
      })
      .catch(err => {
        console.error(err);
        alert("Error: Could not take screenshot.");
      })
      .finally(() => {
        // Reset button text
        if (btnText) btnText.innerText = "Capture";
      });
  };

  // --- UI COMPONENTS ---
  const StatusBadge = ({ label, active, icon: Icon, color = "green" }) => (
    <div className="flex-shrink-0 flex items-center gap-3 bg-slate-800/50 p-3 rounded-xl border border-slate-700 min-w-[140px]">
      <div className={`p-2 rounded-lg ${active ? `bg-${color}-500/20 text-${color}-400` : 'bg-slate-700 text-slate-500'}`}>
        <Icon size={20} />
      </div>
      <div>
        <p className="text-[10px] uppercase text-slate-400 font-bold tracking-wider">{label}</p>
        <p className={`text-sm font-bold ${active ? 'text-white' : 'text-slate-500'}`}>
          {active ? 'ONLINE' : 'OFFLINE'}
        </p>
      </div>
    </div>
  );

  return (
    <div className="p-4 lg:p-6 max-w-[1600px] mx-auto text-slate-200 min-h-screen pb-20">
      
      {/* 1. Header & Status */}
      <div className="flex flex-col gap-4 mb-6">
        <div className="bg-slate-800 p-4 rounded-2xl border border-slate-700 flex flex-row items-center justify-between gap-4">
             <label className="text-xs font-bold text-slate-500 uppercase whitespace-nowrap">Server IP</label>
             <input 
                type="text" 
                value={serverIP}
                onChange={(e) => setServerIP(e.target.value)}
                className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white font-mono w-full text-sm"
             />
        </div>

        <div className="flex gap-4 overflow-x-auto pb-2 scrollbar-hide">
            <StatusBadge label="Camera" active={systemHealth?.camera} icon={Video} />
            <StatusBadge label="MQTT Link" active={systemHealth?.mqtt} icon={Wifi} color="blue" />
            <StatusBadge label="Recording" active={systemHealth?.recording} icon={Mic} color="red" />
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* 2. Main Video Feed */}
        <div className="lg:col-span-2 space-y-4 lg:space-y-6">
            <div className="relative overflow-hidden rounded-2xl border border-slate-700 bg-black shadow-2xl">
                <div className="absolute top-4 left-4 bg-red-600/90 text-white text-[10px] font-bold px-3 py-1 rounded-full animate-pulse z-10">
                    LIVE FEED
                </div>
                <div className="aspect-video w-full bg-slate-950 flex items-center justify-center">
                    <img 
                        src={`${API_BASE}/video_feed`}
                        alt="Live Stream"
                        className="w-full h-full object-contain"
                        onError={(e) => { e.target.style.display='none'; }} 
                    />
                    <div className="absolute inset-0 flex items-center justify-center -z-10">
                        <span className="text-slate-600 font-mono text-sm">Connecting to stream...</span>
                    </div>
                </div>
            </div>

            {/* Control Buttons */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 lg:gap-4">
                <button onClick={() => sendCommand("open_big")} className="p-4 bg-blue-600 active:bg-blue-700 text-white rounded-xl font-bold shadow-lg flex flex-col items-center justify-center gap-2 h-24 lg:h-auto">
                    <ShieldCheck size={24} />
                    <span className="text-sm">Open Gate</span>
                </button>

                {/* TOGGLE LIGHT BUTTON */}
                <button 
                    onClick={toggleLight} 
                    className={`p-4 rounded-xl font-bold shadow-lg flex flex-col items-center justify-center gap-2 h-24 lg:h-auto transition-all ${
                        lightOn 
                        ? "bg-yellow-500 text-slate-900 hover:bg-yellow-400"  // ON Style
                        : "bg-slate-700 text-slate-300 hover:bg-slate-600"   // OFF Style
                    }`}
                >
                    {lightOn ? <Lightbulb size={24} /> : <LightbulbOff size={24} />}
                    <span className="text-sm">{lightOn ? "Light ON" : "Light OFF"}</span>
                </button>

                <button 
                    onClick={handleCapture} 
                    className="p-4 bg-purple-600 active:bg-purple-700 text-white rounded-xl font-bold shadow-lg flex flex-col items-center justify-center gap-2 h-24 lg:h-auto"
                >
                    <Camera size={24} />
                    {/* ADD id="capture-text" HERE */}
                    <span id="capture-text" className="text-sm">Capture</span>
                </button>

                <button onClick={() => sendCommand("close_gate")} className="p-4 bg-red-600 active:bg-red-700 text-white rounded-xl font-bold shadow-lg flex flex-col items-center justify-center gap-2 h-24 lg:h-auto">
                    <Power size={24} />
                    <span className="text-sm">Close Gate</span>
                </button>
            </div>
        </div>

        {/* 3. Instructions / Logs */}
        <div className="bg-slate-800 rounded-2xl border border-slate-700 p-4 lg:p-6 h-fit">
            <h3 className="font-bold text-white mb-4 flex items-center gap-2 text-lg">
                <Settings className="text-emerald-400" /> Control Panel
            </h3>
            
            <div className="p-4 bg-slate-900 rounded-xl border border-slate-800">
                <h4 className="text-xs font-bold text-slate-500 uppercase mb-3">Debug Actions</h4>
                <div className="grid grid-cols-2 gap-3">
                    <button onClick={() => sendCommand("test_log")} className="py-2 bg-slate-700 text-xs rounded hover:bg-slate-600 text-slate-200">Test Log</button>
                    <button onClick={() => sendCommand("reset")} className="py-2 bg-slate-700 text-xs rounded hover:bg-slate-600 text-slate-200">Reset AI</button>
                </div>
            </div>
        </div>

      </div>
    </div>
  );
};

export default CameraPage;