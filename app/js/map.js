  function drawMap(containerId, routeFilter) {
    const el = qs(containerId);
    if (!el) return;
    // If Leaflet is available, render an interactive map; else fall back to SVG renderer
    if (typeof L !== 'undefined') {
      // initialize map if needed
      if (!state.maps[containerId]) {
        const map = L.map(containerId, { zoomControl: true, attributionControl: false }).setView([10.3157, 123.8854], 13);
        const tileLayer = L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
          attribution: '&copy; OpenStreetMap contributors'
        }).addTo(map);
        tileLayer.on('tileerror', function(e) {
          if (e.tile) e.tile.style.display = 'none';
        });
        state.maps[containerId] = map;
        state.mapLayers[containerId] = L.layerGroup().addTo(map);
        addMapActionControl(containerId, map);
        // clustering layer
        try {
          state.mapClusters[containerId] = L.markerClusterGroup({
            iconCreateFunction(cluster) {
              const markers = cluster.getAllChildMarkers();
              const overloaded = markers.filter(marker => marker.options.loadsenseTier === "blinking_red").length;
              const label = overloaded ? `${markers.length}/${overloaded}` : String(markers.length);
              return L.divIcon({ html: `<div><span>${label}</span></div>`, className: "marker-cluster marker-cluster-small", iconSize: L.point(40, 40) });
            },
          });
          state.mapClusters[containerId].addTo(map);
        } catch (e) {
          state.mapClusters[containerId] = null;
        }
      }
      const map = state.maps[containerId];
      const layerGroup = state.mapLayers[containerId];
      const clusterGroup = state.mapClusters[containerId];
      // clear previous layers
      layerGroup.clearLayers();
      if (clusterGroup && clusterGroup.clearLayers) clusterGroup.clearLayers();

      const routes = routeFilter ? state.routes.filter(route => route.route === routeFilter) : state.routes;
      // draw route polylines
      for (const route of routes) {
        const latlngs = (route.polyline || []).map(getCoordinate).filter(Boolean).map(c => [c.latitude, c.longitude]);
        if (latlngs.length) {
            const selectedRoute = route.route === state.selectedRoute;
            if (selectedRoute) {
              L.polyline(latlngs, { color: '#ffffff', weight: 12, opacity: 0.95, lineCap: 'round', lineJoin: 'round' }).addTo(layerGroup);
              L.polyline(latlngs, { color: '#0b57d0', weight: 8, opacity: 0.98, lineCap: 'round', lineJoin: 'round' }).addTo(layerGroup);
              L.polyline(latlngs, { color: '#58a6ff', weight: 3, opacity: 0.95, lineCap: 'round', lineJoin: 'round' }).addTo(layerGroup);
              
              const stops = (route.stops || []).map((stop, i) => ({ coord: getCoordinate(stop), name: stop.name || `Stop ${i + 1}` })).filter(s => s.coord);
              stops.forEach(stop => {
                const marker = L.circleMarker([stop.coord.latitude, stop.coord.longitude], {
                  radius: 5, color: '#1e293b', weight: 2, fillColor: '#ffffff', fillOpacity: 1
                }).bindTooltip(escapeHtml(stop.name), { direction: 'top', offset: [0, -5] });
                marker.addTo(layerGroup);
              });
            } else {
              L.polyline(latlngs, { color: '#9aa0a6', weight: 2, opacity: routeFilter ? 0.25 : 0.16, lineCap: 'round', lineJoin: 'round' }).addTo(layerGroup);
            }
            // start and end markers
            const start = latlngs[0];
            const end = latlngs[latlngs.length-1];
            const startMarker = L.circleMarker(start, { radius: 6, color: '#fff', weight: 1, fillColor: '#045c51', fillOpacity: 1 }).bindTooltip('Start');
            const endMarker = L.circleMarker(end, { radius: 6, color: '#fff', weight: 1, fillColor: '#2f5f98', fillOpacity: 1 }).bindTooltip('End');
            startMarker.addTo(layerGroup);
            endMarker.addTo(layerGroup);
        }
      }
      // draw vehicle markers
      const vehicles = state.vehicles.filter(vehicle => !routeFilter || vehicle.route === routeFilter).filter(vehicle => Number(vehicle.latitude) && Number(vehicle.longitude));
      for (const vehicle of vehicles) {
        const lat = Number(vehicle.latitude);
        const lon = Number(vehicle.longitude);
        const tier = tierClass(vehicle.tier);
        const icon = L.divIcon({ className: 'vehicle-icon-wrapper', html: `<span class="vehicle-div-icon ${tier}"></span>`, iconSize: [18,18], iconAnchor: [9,9] });
        const marker = L.marker([lat, lon], { icon, loadsenseTier: vehicle.tier });
        const popup = `<strong>${escapeHtml(vehicle.vehicle_id)}</strong><br/>Route: ${escapeHtml(vehicle.route)}<br/>Load: ${escapeHtml(String(vehicle.occupancy))}/${escapeHtml(String(vehicle.capacity))}<br/>ETA: ${escapeHtml(String(vehicle.eta_minutes))} min<br/><button onclick="window.LoadSense.zoomVehicle('${escapeHtml(vehicle.vehicle_id)}')">Zoom to PUV</button><button onclick="window.LoadSense.createAlert('${escapeHtml(vehicle.vehicle_id)}','${escapeHtml(vehicle.route)}')">Flag incident</button>`;
        marker.bindPopup(popup);
        marker.bindTooltip(`${escapeHtml(vehicle.vehicle_id)} (${escapeHtml(vehicle.route)})` , { permanent: false });
        if (clusterGroup) {
          clusterGroup.addLayer(marker);
        } else {
          marker.addTo(layerGroup);
        }
      }
      drawDestinationLayer(containerId, layerGroup);
      setTimeout(() => { try { map.invalidateSize(); } catch (e) {} }, 150);
      return;
    }
    // Fallback: original SVG renderer
    const routes = routeFilter ? state.routes.filter(route => route.route === routeFilter) : state.routes;
    const bounds = routeBounds(routes.length ? routes : state.routes);
    const routeLines = routes.map(route => {
      const points = (route.polyline || []).map(getCoordinate).filter(Boolean).map(point => project(point, bounds));
      const d = points.map((point, index) => `${index ? "L" : "M"} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`).join(" ");
      const stops = points.map(point => `<circle class="map-stop" cx="${point.x}" cy="${point.y}" r="1.6"></circle>`).join("");
      return `<path class="map-route" d="${d}"></path>${stops}`;
    }).join("");
    const vehicles = state.vehicles
      .filter(vehicle => !routeFilter || vehicle.route === routeFilter)
      .filter(vehicle => Number(vehicle.latitude) && Number(vehicle.longitude))
      .map(vehicle => {
        const point = project({ latitude: vehicle.latitude, longitude: vehicle.longitude }, bounds);
        return `
          <g class="map-pin">
            <circle class="${tierClass(vehicle.tier)}" cx="${point.x}" cy="${point.y}" r="3.4"></circle>
            <text x="${point.x}" y="${point.y + 1.1}">${escapeHtml(vehicle.vehicle_id.split("-").pop())}</text>
          </g>
        `;
      }).join("");

    el.innerHTML = `
      <svg viewBox="0 0 100 100" role="img" aria-label="Route map with live PUV positions">
        <defs>
          <pattern id="${containerId}-grid" width="10" height="10" patternUnits="userSpaceOnUse">
            <path d="M 10 0 L 0 0 0 10" fill="none" stroke="rgba(30,45,60,.08)" stroke-width=".4"></path>
          </pattern>
        </defs>
        <rect width="100" height="100" fill="url(#${containerId}-grid)"></rect>
        ${routeLines}
        ${vehicles}
      </svg>
    `;
  }

  function addMapActionControl(containerId, map) {
    if (typeof L === "undefined") return;
    const control = L.control({ position: "topright" });
    control.onAdd = function () {
      const wrap = L.DomUtil.create("div", "map-action-control");
      const button = L.DomUtil.create("button", "", wrap);
      button.type = "button";
      button.title = containerId === "operatorMap" ? "Center map on fleet" : "Center map on my location";
      button.setAttribute("aria-label", button.title);
      button.textContent = containerId === "operatorMap" ? "Fit" : "Me";
      L.DomEvent.disableClickPropagation(wrap);
      L.DomEvent.on(button, "click", () => {
        if (containerId === "operatorMap") {
          fitFleet(containerId);
        } else if (state.lastPosition) {
          map.setView([state.lastPosition.latitude, state.lastPosition.longitude], 15);
        } else {
          fitRoute(containerId, state.selectedRoute);
        }
      });
      return wrap;
    };
    control.addTo(map);
  }

  function drawDestinationLayer(containerId, layerGroup) {
    if (containerId !== "mobileMap" || typeof L === "undefined" || !state.selectedDestination) return;
    const destination = [state.selectedDestination.latitude, state.selectedDestination.longitude];
    L.marker(destination, {
      icon: L.divIcon({ className: "destination-marker", html: "<span></span>", iconSize: [24, 24], iconAnchor: [12, 22] }),
    }).bindTooltip("Destination").addTo(layerGroup);
    const best = state.vehicles.filter(v => v.route === state.selectedRoute && Number(v.latitude) && Number(v.longitude)).sort(vehicleSort)[0];
    if (best) {
      L.polyline([[Number(best.latitude), Number(best.longitude)], destination], { color: "#0f766e", weight: 4, dashArray: "8 8", opacity: 0.8 }).addTo(layerGroup);
    }
  }

  function renderVehicleCard(vehicle) {
    return `
      <article class="vehicle-card">
        <div>
          <h4>${escapeHtml(vehicle.vehicle_id)} <span>Route ${escapeHtml(vehicle.route)}</span></h4>
          <p>${escapeHtml(routeName(vehicle.route))}</p>
          <p>ETA ${vehicle.eta_minutes} min to Stop ${Number(vehicle.next_stop_id) + 1} - ${vehicle.occupancy}/${vehicle.capacity} riders - ${escapeHtml(vehicle.status || "active")}</p>
        </div>
        <div class="vehicle-card-actions">
          <span class="occupancy-pill ${tierClass(vehicle.tier)}">${tierLabel(vehicle.tier)}</span>
          <button class="mini-action" data-zoom-vehicle="${escapeHtml(vehicle.vehicle_id)}">Zoom</button>
        </div>
      </article>
    `;
  }

