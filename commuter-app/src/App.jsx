import React, { useEffect, useState } from 'react';
import { createRoot } from 'react-dom/client';
import { Bot, List, Map } from 'lucide-react';
import 'leaflet/dist/leaflet.css';
import './styles.css';
import StopView from './pages/StopView';
import MapView from './pages/MapView';
import Chatbot from './pages/Chatbot';
export const API = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000';
function App(){const[tab,setTab]=useState('stops');const[stops,setStops]=useState([]);const[selectedStop,setSelectedStop]=useState('ayala');const[fleet,setFleet]=useState([]);const refresh=()=>fetch(`${API}/api/fleet`).then(r=>r.json()).then(setFleet).catch(()=>setFleet([]));useEffect(()=>{fetch(`${API}/api/stops`).then(r=>r.json()).then(d=>{setStops(d);if(d[0])setSelectedStop(d[0].id)}).catch(()=>{});refresh();const id=setInterval(refresh,3000);return()=>clearInterval(id)},[]);const page=tab==='map'?<MapView stops={stops} selectedStop={selectedStop} fleet={fleet}/>:tab==='chat'?<Chatbot selectedStop={selectedStop}/>:<StopView stops={stops} selectedStop={selectedStop} setSelectedStop={setSelectedStop} fleet={fleet}/>;return <div className="stage"><div className="phone"><header><strong>LoadSense</strong><span>Powered by SDG 9 + SDG 11</span></header>{page}<nav className="tabs"><button className={tab==='stops'?'active':''} onClick={()=>setTab('stops')}><List size={19}/>Stops</button><button className={tab==='map'?'active':''} onClick={()=>setTab('map')}><Map size={19}/>Map</button><button className={tab==='chat'?'active':''} onClick={()=>setTab('chat')}><Bot size={19}/>Chat</button></nav></div></div>}
createRoot(document.getElementById('root')).render(<App/>);
