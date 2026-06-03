(function () {
  const api = `${location.origin}/api`;
  const state = {
    vehicles: [],
    routes: [],
    alerts: [],
    demand: {},
    database: {},
    incidents: [],
    selectedRoute: "04L",
    maps: {},
    mapLayers: {},
  };

  const tierCopy = {
    green: "Seats available",
    yellow: "Standing only",
    red: "At capacity",
    blinking_red: "Overloaded",
  };

  function qs(id) {
    return document.getElementById(id);
  }

  async function getJson(path, options) {
    const response = await fetch(api + path, options);
    if (!response.ok) throw new Error(await response.text());
    return response.json();
  }

  function escapeHtml(value) {
    return String(value ?? "")
      .replaceAll("&", "&amp;")
      .replaceAll("<", "&lt;")
      .replaceAll(">", "&gt;")
      .replaceAll('"', "&quot;")
      .replaceAll("'", "&#039;");
  }

  function tierClass(tier) {
    return ["green", "yellow", "red", "blinking_red"].includes(tier) ? tier : "neutral";
  }

  function tierLabel(tier) {
    return tierCopy[tier] || "No signal";
  }

  function vehicleSort(a, b) {
    const rank = { green: 0, yellow: 1, red: 2, blinking_red: 3 };
    return (rank[a.tier] ?? 9) - (rank[b.tier] ?? 9) || a.eta_minutes - b.eta_minutes;
  }

  async function seedDemoData() {
    const now = new Date().toISOString();
    const payloads = [
      ["J-214", "04L", 14.5992, 120.9840, 7, 21, "ok"],
      ["J-102", "04L", 14.6001, 120.9850, 14, 18, "ok"],
      ["J-330", "08A", 14.5996, 120.9846, 17, 14, "ok"],
      ["J-417", "12B", 14.6100, 120.9950, 10, 24, "ok"],
      ["J-808", "17C", 0, 0, 5, 0, "gps_dropout"],
    ];
    for (const [vehicle_id, route, latitude, longitude, occupancy, speed_kph, signal_quality] of payloads) {
      await getJson("/telemetry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ vehicle_id, route, latitude, longitude, occupancy, speed_kph, signal_quality, timestamp: now }),
      });
    }
    await refreshData();
  }

  async function refreshData() {
    const [fleet, routes, alerts, demand, database, incidents] = await Promise.all([
      getJson("/fleet"),
      getJson("/routes"),
      getJson("/alerts"),
      getJson("/demand"),
      getJson("/database/status"),
      getJson("/incidents"),
    ]);
    state.vehicles = fleet.vehicles || [];
    state.summary = fleet.summary || {};
    state.routes = routes.routes || [];
    state.alerts = alerts.alerts || [];
    state.demand = demand || {};
    state.database = database || {};
    state.incidents = incidents.incidents || [];
    return state;
  }

  function routeName(routeId) {
    return state.routes.find(route => route.route === routeId)?.name || routeId;
  }

  function selectOptions(selected) {
    return state.routes.map(route => {
      const attr = route.route === selected ? " selected" : "";
      return `<option value="${escapeHtml(route.route)}"${attr}>${escapeHtml(route.route)} ${escapeHtml(route.name)}</option>`;
    }).join("");
  }

  function routeBounds(routes) {
    const points = routes.flatMap(route => route.polyline || []);
    const valid = points.filter(point => Number(point.latitude) && Number(point.longitude));
    if (!valid.length) {
      return { minLat: 14.598, maxLat: 14.602, minLon: 120.983, maxLon: 120.988 };
    }
    const lats = valid.map(point => point.latitude);
    const lons = valid.map(point => point.longitude);
    return {
      minLat: Math.min(...lats),
      maxLat: Math.max(...lats),
      minLon: Math.min(...lons),
      maxLon: Math.max(...lons),
    };
  }

  function project(point, bounds) {
    const latRange = Math.max(0.0001, bounds.maxLat - bounds.minLat);
    const lonRange = Math.max(0.0001, bounds.maxLon - bounds.minLon);
    return {
      x: 8 + ((point.longitude - bounds.minLon) / lonRange) * 84,
      y: 88 - ((point.latitude - bounds.minLat) / latRange) * 76,
    };
  }

  function drawMap(containerId, routeFilter) {
    const el = qs(containerId);
    if (!el) return;
    // If Leaflet is available, render an interactive map; else fall back to SVG renderer
    if (typeof L !== 'undefined') {
      // initialize map if needed
      if (!state.maps[containerId]) {
        // default center near Cebu
        const map = L.map(containerId, { zoomControl: false }).setView([14.5992, 120.9840], 13);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
          maxZoom: 19,
        }).addTo(map);
        state.maps[containerId] = map;
        state.mapLayers[containerId] = L.layerGroup().addTo(map);
      }
      const map = state.maps[containerId];
      const layerGroup = state.mapLayers[containerId];
      // clear previous layers
      layerGroup.clearLayers();

      const routes = routeFilter ? state.routes.filter(route => route.route === routeFilter) : state.routes;
      const pointsAll = [];
      // draw route polylines
      for (const route of routes) {
        const latlngs = (route.polyline || []).filter(p => Number(p.latitude) && Number(p.longitude)).map(p => [Number(p.latitude), Number(p.longitude)]);
        if (latlngs.length) {
          L.polyline(latlngs, { color: '#2f5f98', weight: 3 }).addTo(layerGroup);
          pointsAll.push(...latlngs);
        }
      }
      // draw vehicle markers
      const vehicles = state.vehicles.filter(vehicle => !routeFilter || vehicle.route === routeFilter).filter(vehicle => Number(vehicle.latitude) && Number(vehicle.longitude));
      for (const vehicle of vehicles) {
        const lat = Number(vehicle.latitude);
        const lon = Number(vehicle.longitude);
        const color = tierClass(vehicle.tier) === 'green' ? '#16865d' : tierClass(vehicle.tier) === 'yellow' ? 'var(--amber)' : '#c93b31';
        const marker = L.circleMarker([lat, lon], { radius: 6, color: '#fff', weight: 1, fillColor: color, fillOpacity: 1 });
        marker.bindTooltip(`${escapeHtml(vehicle.vehicle_id)} (${escapeHtml(vehicle.route)})` , { permanent: false });
        marker.addTo(layerGroup);
        pointsAll.push([lat, lon]);
      }
      // adjust view to bounds if we have points
      if (pointsAll.length) {
        try {
          const bounds = L.latLngBounds(pointsAll);
          map.fitBounds(bounds.pad ? bounds.pad(0.2) : bounds, { maxZoom: 16 });
        } catch (e) {
          // ignore
        }
      }
      return;
    }
    // Fallback: original SVG renderer
    const routes = routeFilter ? state.routes.filter(route => route.route === routeFilter) : state.routes;
    const bounds = routeBounds(routes.length ? routes : state.routes);
    const routeLines = routes.map(route => {
      const points = (route.polyline || []).map(point => project(point, bounds));
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

  function renderVehicleCard(vehicle) {
    return `
      <article class="vehicle-card">
        <div>
          <h4>${escapeHtml(vehicle.vehicle_id)} <span>Route ${escapeHtml(vehicle.route)}</span></h4>
          <p>${escapeHtml(routeName(vehicle.route))}</p>
          <p>ETA ${vehicle.eta_minutes} min to Stop ${Number(vehicle.next_stop_id) + 1} - ${vehicle.occupancy}/${vehicle.capacity} riders</p>
        </div>
        <span class="occupancy-pill ${tierClass(vehicle.tier)}">${tierLabel(vehicle.tier)}</span>
      </article>
    `;
  }

  function initMobileTabs() {
    document.querySelectorAll(".mobile-nav button").forEach(button => {
      button.addEventListener("click", () => {
        document.querySelectorAll(".mobile-nav button").forEach(item => item.classList.remove("active"));
        document.querySelectorAll(".tab-panel").forEach(item => item.classList.remove("active"));
        button.classList.add("active");
        qs(button.dataset.tab).classList.add("active");
      });
    });
  }

  function renderMobile() {
    const selected = state.selectedRoute;
    qs("mobileRouteTitle").textContent = `Route ${selected}`;
    const mapRoute = qs("mapRoute");
    if (mapRoute) {
      mapRoute.innerHTML = selectOptions(selected);
      mapRoute.value = selected;
    }
    const homeRoute = qs("homeRouteSelect");
    if (homeRoute) {
      homeRoute.innerHTML = selectOptions(selected);
      homeRoute.value = selected;
    }

    const routeVehicles = state.vehicles.filter(vehicle => vehicle.route === selected).sort(vehicleSort);
    const best = routeVehicles[0] || [...state.vehicles].sort(vehicleSort)[0];
    qs("mobileFleet").innerHTML = routeVehicles.length
      ? routeVehicles.map(renderVehicleCard).join("")
      : `<p class="empty-copy">No live PUVs for Route ${escapeHtml(selected)}. Seed demo data or start mock telemetry.</p>`;

    if (best) {
      const safeText = best.route_deviation?.anomaly ? "Verify" : "Clear";
      qs("bestVehicleTitle").textContent = `${best.vehicle_id} - ${tierLabel(best.tier)}`;
      qs("bestVehicleBody").textContent = `ETA ${best.eta_minutes} min near Stop ${Number(best.next_stop_id) + 1}. ${best.route_deviation?.anomaly ? "Operator verification is needed before passenger alerting." : "Route is currently within the expected corridor."}`;
      qs("ledPill").className = `occupancy-pill ${tierClass(best.tier)}`;
      qs("ledPill").textContent = `Windshield LED: ${tierLabel(best.tier)}`;
      qs("homeEta").textContent = `${best.eta_minutes}m`;
      qs("homeLoad").textContent = `${best.occupancy}/${best.capacity}`;
      qs("homeSafety").textContent = safeText;
    }

    qs("routeList").innerHTML = state.routes.map(route => `
      <article class="route-card">
        <div>
          <h3>${escapeHtml(route.route)} ${escapeHtml(route.name)}</h3>
          <p>${route.stops.length} tracked stops - ${state.vehicles.filter(vehicle => vehicle.route === route.route).length} live PUVs</p>
        </div>
        <ol>
          ${route.stops.map(stop => `<li>${escapeHtml(stop.name)}</li>`).join("")}
        </ol>
      </article>
    `).join("");
    drawMap("mobileMap", selected);
  }

  async function askMobileChat(query) {
    const transcript = qs("chatTranscript");
    transcript.insertAdjacentHTML("beforeend", `<div class="message user">${escapeHtml(query)}</div>`);
    const result = await getJson("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ route: state.selectedRoute, query }),
    });
    transcript.insertAdjacentHTML("beforeend", `<div class="message bot">${escapeHtml(result.answer)}</div>`);
    transcript.scrollTop = transcript.scrollHeight;
  }

  async function initMobile() {
    initMobileTabs();
    qs("loginForm").addEventListener("submit", async event => {
      event.preventDefault();
      // Login only collects mobile number; route selection moved to Home tab
      qs("loginScreen").classList.add("hidden");
      qs("appScreen").classList.remove("hidden");
      await refreshData();
      renderMobile();
    });
    qs("mapRoute").addEventListener("change", event => {
      state.selectedRoute = event.target.value;
      renderMobile();
    });
    // Home route selector (moved from login)
    const homeRouteSelect = qs("homeRouteSelect");
    if (homeRouteSelect) {
      homeRouteSelect.addEventListener("change", event => {
        state.selectedRoute = event.target.value;
        renderMobile();
      });
    }
    qs("seedMobile").addEventListener("click", async () => {
      await seedDemoData();
      renderMobile();
    });
    qs("refreshMobile").addEventListener("click", async () => {
      await refreshData();
      renderMobile();
    });
    qs("chatForm").addEventListener("submit", async event => {
      event.preventDefault();
      const input = qs("chatInput");
      const query = input.value.trim();
      if (!query) return;
      input.value = "";
      await askMobileChat(query);
    });
  }

  function renderForecast() {
    const rows = (state.demand.forecast || []).slice(0, 24);
    const max = Math.max(1, ...rows.map(row => row.expected_load || 0));
    qs("forecastBars").innerHTML = rows.length
      ? rows.map(row => `
          <span class="forecast-bar" title="${escapeHtml(row.route)} ${row.expected_load}" style="height:${Math.max(8, (row.expected_load / max) * 100)}%">
            <b>${escapeHtml(row.route)}</b>
          </span>
        `).join("")
      : `<p class="empty-copy">No forecast artifact found.</p>`;
    qs("forecastMeta").textContent = rows.length
      ? `${state.demand.model || "forecast"} - generated ${state.demand.generated_at || "from checked-in artifact"}`
      : "";
  }

  function renderOperator() {
    qs("opVehicleCount").textContent = state.summary.vehicle_count ?? 0;
    qs("opAlertCount").textContent = state.summary.active_alerts ?? 0;
    qs("opAvgLoad").textContent = state.summary.average_occupancy ?? 0;
    qs("opOverloaded").textContent = state.summary.overloaded ?? 0;
    qs("operatorFleet").innerHTML = state.vehicles.length
      ? state.vehicles.map(vehicle => `
          <article>
            <div>
              <h3>${escapeHtml(vehicle.vehicle_id)}</h3>
              <p>Route ${escapeHtml(vehicle.route)} - ${escapeHtml(routeName(vehicle.route))}</p>
            </div>
            <span>${vehicle.eta_minutes} min</span>
            <span>${vehicle.occupancy}/${vehicle.capacity}</span>
            <span class="occupancy-pill ${tierClass(vehicle.tier)}">${tierLabel(vehicle.tier)}</span>
            <span>${vehicle.route_deviation?.anomaly ? "Verify route" : "On route"}</span>
          </article>
        `).join("")
      : `<p class="empty-copy">No telemetry received yet.</p>`;

    qs("operatorAlerts").innerHTML = state.alerts.length
      ? state.alerts.map(alert => `
          <article class="alert-card ${escapeHtml(alert.severity)}">
            <div>
              <h3>${escapeHtml(alert.severity).toUpperCase()} - ${escapeHtml(alert.vehicle_id)}</h3>
              <p>${escapeHtml(alert.message)}</p>
              <small>Route ${escapeHtml(alert.route)} - ${new Date(alert.timestamp).toLocaleTimeString()}</small>
            </div>
            <button class="button secondary ack-button" data-alert="${escapeHtml(alert.id)}">Verify</button>
          </article>
        `).join("")
      : `<p class="empty-copy">No active operator alerts.</p>`;
    document.querySelectorAll(".ack-button").forEach(button => {
      button.addEventListener("click", async () => {
        await getJson(`/alerts/${button.dataset.alert}/ack`, { method: "POST" });
        await refreshData();
        renderOperator();
      });
    });
    drawMap("operatorMap");
    renderForecast();
    renderDatabaseStatus();
    renderIncidentLog();
    renderRoutesAdmin();
  }

  function renderRoutesAdmin() {
    const container = qs('routesTable');
    if (!container) return;
    if (!state.routes || !state.routes.length) {
      container.innerHTML = '<p class="empty-copy">No routes found.</p>';
      return;
    }
    container.innerHTML = state.routes.map(r => `
      <article class="route-card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <h3>${escapeHtml(r.route)} ${escapeHtml(r.name)}</h3>
            <p>${(r.stops||[]).length} stops</p>
          </div>
          <div>
            <button class="button secondary edit-route" data-route="${escapeHtml(r.route)}">Edit</button>
            <button class="button" style="background:#f8d7da;color:#7a191b;margin-left:8px" data-route="${escapeHtml(r.route)}" class="delete-route">Delete</button>
          </div>
        </div>
      </article>
    `).join('');
    document.querySelectorAll('.edit-route').forEach(btn => btn.addEventListener('click', e => {
      const route = btn.dataset.route;
      const r = state.routes.find(x => x.route === route);
      if (!r) return;
      qs('routeId').value = r.route;
      qs('routeName').value = r.name;
      qs('routePolyline').value = (r.polyline || []).map(p => `${p.latitude},${p.longitude}`).join('\n');
    }));
    document.querySelectorAll('[data-route]').forEach(btn => {
      if (btn.classList.contains('delete-route') || btn.textContent.trim().toLowerCase()==='delete') {
        btn.addEventListener('click', async () => {
          const route = btn.dataset.route;
          if (!confirm(`Delete route ${route}?`)) return;
          await fetch(api + `/routes/${route}`, { method: 'DELETE' });
          await refreshData();
          renderOperator();
        });
      }
    });
  }

  async function initRoutesAdmin() {
    const save = qs('saveRoute');
    const clear = qs('clearRoute');
    if (save) {
      save.addEventListener('click', async () => {
        const route = qs('routeId').value.trim();
        const name = qs('routeName').value.trim();
        const polytext = qs('routePolyline').value.trim();
        if (!route || !name) { alert('Route and name required'); return; }
        const poly = polytext.split('\n').map(line => line.trim()).filter(Boolean).map(line => {
          const [lat, lon] = line.split(',').map(s => parseFloat(s.trim()));
          return [lat, lon];
        });
        await fetch(api + '/routes', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ route, name, polyline: poly }) });
        qs('routeId').value = '';
        qs('routeName').value = '';
        qs('routePolyline').value = '';
        await refreshData();
        renderOperator();
      });
    }
    if (clear) {
      clear.addEventListener('click', () => {
        qs('routeId').value = '';
        qs('routeName').value = '';
        qs('routePolyline').value = '';
      });
    }
  }

  function renderDatabaseStatus() {
    const tables = state.database.tables || {};
    qs("databaseStatus").innerHTML = Object.keys(tables).length
      ? Object.entries(tables).map(([name, count]) => `
          <article>
            <span>${escapeHtml(name)}</span>
            <strong>${count}</strong>
          </article>
        `).join("") + `<p class="db-path">${escapeHtml(state.database.path || "")}</p>`
      : `<p class="empty-copy">Database has not been initialized.</p>`;
  }

  function renderIncidentLog() {
    qs("incidentLog").innerHTML = state.incidents.length
      ? state.incidents.slice(0, 8).map(incident => `
          <article>
            <div>
              <h3>${escapeHtml(incident.vehicle_id)} - ${escapeHtml(incident.severity).toUpperCase()}</h3>
              <p>${escapeHtml(incident.message)}</p>
            </div>
            <span>${incident.acknowledged ? "Verified" : "Open"}</span>
          </article>
        `).join("")
      : `<p class="empty-copy">No incident history yet.</p>`;
  }

  async function initOperator() {
    await refreshData();
    renderOperator();
    await initRoutesAdmin();
    qs("seedOperator").addEventListener("click", async () => {
      await seedDemoData();
      renderOperator();
    });
    qs("refreshOperator").addEventListener("click", async () => {
      await refreshData();
      renderOperator();
    });
    setInterval(async () => {
      await refreshData();
      renderOperator();
    }, 5000);
  }

  window.LoadSense = { initMobile, initOperator };
})();
