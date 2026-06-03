import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { AlertTriangle, BarChart3, Bus, ClipboardList, Map } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import './styles.css';
import FleetMap from './pages/FleetMap';
import Alerts from './pages/Alerts';
import Demand from './pages/Demand';
import Incidents from './pages/Incidents';
export const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
function App() {
  const [page, setPage] = useState('fleet');
  const [fleet, setFleet] = useState([]);
  const [alerts, setAlerts] = useState([]);
  const refresh = async () => {
    const [f, a] = await Promise.all([fetch(`${API}/api/fleet`).then(r => r.json()).catch(() => []), fetch(`${API}/api/anomalies`).then(r => r.json()).catch(() => [])]);
    setFleet(f); setAlerts(a);
  };
  useEffect(() => { refresh(); const id = setInterval(refresh, 2000); return () => clearInterval(id); }, []);
  const pending = alerts.filter(a => a.status === 'pending_operator_review').length;
  const nav = [['fleet', Map, 'Fleet Map'], ['alerts', AlertTriangle, 'Alerts'], ['demand', BarChart3, 'Demand'], ['incidents', ClipboardList, 'Incidents']];
  return <div className="shell"><aside className="sidebar"><div className="brand"><Bus size={26}/><div><strong>LoadSense</strong><span>Control room</span></div></div><nav>{nav.map(([key, Icon, label]) => <button className={page === key ? 'active' : ''} onClick={() => setPage(key)} key={key}><Icon size={18}/>{label}{key === 'alerts' && pending > 0 && <b>{pending}</b>}</button>)}</nav><div className="route-badges"><span>Ayala-SM-Carbon</span><span>Colon-Talamban</span><span>Basak-Pardo</span></div><footer>{fleet.length} live vehicles<br/>Powered by SDG 9 + SDG 11</footer></aside><main>{page === 'fleet' && <FleetMap fleet={fleet}/>} {page === 'alerts' && <Alerts alerts={alerts} onRefresh={refresh}/>} {page === 'demand' && <Demand/>} {page === 'incidents' && <Incidents alerts={alerts}/>}</main></div>;
}
createRoot(document.getElementById('root')).render(<App />);
