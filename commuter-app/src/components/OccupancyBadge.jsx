import React from 'react';
const colors={GREEN:'#22c55e',YELLOW:'#eab308',RED:'#ef4444',BLINKING_RED:'#ef4444'};
export default function OccupancyBadge({tier}){return <span className={`badge ${tier==='BLINKING_RED'?'pulse':''}`} style={{background:colors[tier]||'#64748b'}}>{tier}</span>}
