import React from 'react';
const colors = { GREEN: '#22c55e', YELLOW: '#eab308', RED: '#ef4444', BLINKING_RED: '#ef4444' };
export default function LEDStrip({ tier = 'GREEN' }) { return <div className={`led ${tier === 'BLINKING_RED' ? 'pulse' : ''}`} style={{ '--tier': colors[tier] }}>{Array.from({ length: 12 }).map((_, i) => <span key={i}/>)}</div>; }
