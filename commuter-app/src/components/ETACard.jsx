import React from 'react';
import OccupancyBadge from './OccupancyBadge';
export default function ETACard({vehicle,eta}){return <article className="eta-card"><div><OccupancyBadge tier={vehicle.occupancy_tier}/><strong>{vehicle.route_name||'Ayala-SM-Carbon'}</strong><small>{vehicle.vehicle_id} · {vehicle.passenger_count}/16 riders</small></div><div className="minutes">{eta}<small> min</small></div></article>}
