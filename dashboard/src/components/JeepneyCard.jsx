import React from 'react';
import LEDStrip from './LEDStrip';
export default function JeepneyCard({ vehicle }) { return <div className="card-row"><strong>{vehicle.vehicle_id}</strong><span>{vehicle.passenger_count}/16 riders</span><LEDStrip tier={vehicle.occupancy_tier}/><span>{vehicle.speed_kph} kph</span><span className="badge">{vehicle.occupancy_tier}</span></div>; }
