  function findNearestRoute(lat, lon) {
    if (!state.routes || !state.routes.length) return null;
    function toRad(x){return x*Math.PI/180}
    function haversine(aLat,aLon,bLat,bLon){
      const R = 6371000;
      const dLat = toRad(bLat - aLat);
      const dLon = toRad(bLon - aLon);
      const A = Math.sin(dLat/2)*Math.sin(dLat/2) + Math.cos(toRad(aLat))*Math.cos(toRad(bLat))*Math.sin(dLon/2)*Math.sin(dLon/2);
      const C = 2 * Math.atan2(Math.sqrt(A), Math.sqrt(1-A));
      return R * C;
    }
    let best = null;
    let bestD = Infinity;
    for (const r of state.routes) {
      const points = (r.polyline || []).map(p => [Number(p.latitude), Number(p.longitude)]);
      for (const [plat, plon] of points) {
        const d = haversine(lat, lon, plat, plon);
        if (d < bestD) { bestD = d; best = r.route; }
      }
    }
    // threshold 1000m to auto-select
    return bestD < 600 ? best : null;
  }

  function setupRecenterButtons() {
    const recenter = qs('recenterBtn');
    const opRecenter = qs('opRecenterBtn');
    if (recenter) recenter.addEventListener('click', () => {
      const map = state.maps['mobileMap'];
      if (!map) return;
      if (state.lastPosition) {
        map.setView([state.lastPosition.latitude, state.lastPosition.longitude], 15);
      } else {
        fitRoute('mobileMap', state.selectedRoute);
      }
    });
    if (opRecenter) opRecenter.addEventListener('click', () => {
      const map = state.maps['operatorMap'];
      if (!map) return;
      fitFleet('operatorMap');
    });
  }

  function fitRoute(containerId, routeId) {
    const map = state.maps[containerId];
    const route = state.routes.find(item => item.route === routeId);
    const points = (route?.polyline || []).filter(isMapCoordinate).map(point => [Number(point.latitude), Number(point.longitude)]);
    if (map && points.length) {
      try { map.fitBounds(L.latLngBounds(points), { maxZoom: 15, padding: [28, 28] }); } catch (e) {}
    }
  }

  function fitFleet(containerId) {
    const map = state.maps[containerId];
    const points = state.vehicles.filter(isMapCoordinate).map(vehicle => [Number(vehicle.latitude), Number(vehicle.longitude)]);
    if (map && points.length) {
      try { map.fitBounds(L.latLngBounds(points), { maxZoom: 15, padding: [28, 28] }); } catch (e) {}
    }
  }

  function previewRoute(routeId, containerId = "operatorMap") {
    const route = state.routes.find(item => item.route === routeId);
    if (!route) return;
    state.selectedRoute = routeId;
    const panel = qs("routePreviewPanel");
    if (panel && containerId === "routePreviewMap") {
      panel.classList.remove("hidden");
      qs("routePreviewTitle").textContent = `${route.route} ${route.name}`;
      const summary = routeSummary(route);
      qs("routePreviewMeta").textContent = `${cityName(route)} - ${summary.stopCount} stops - ${summary.vehicleCount} live PUVs`;
    }
    drawMap(containerId, routeId);
    setTimeout(() => fitRoute(containerId, routeId), 120);
  }

  function zoomVehicle(vehicleId) {
    const vehicle = state.vehicles.find(item => item.vehicle_id === vehicleId);
    if (!vehicle || !isMapCoordinate(vehicle)) return;
    state.selectedVehicleId = vehicleId;
    state.selectedRoute = vehicle.route;
    if (state.maps.operatorMap) activateOperatorTab("opsOverview");
    if (state.maps.mobileMap) activateMobileTab("mapTab");
    drawMap(state.maps.operatorMap ? "operatorMap" : "mobileMap", vehicle.route);
    const map = state.maps.operatorMap || state.maps.mobileMap;
    if (map) {
      setTimeout(() => {
        map.setView([Number(vehicle.latitude), Number(vehicle.longitude)], 17);
      }, 100);
    }
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
        <div class="route-card-admin-row">
          <div>
            <h3>${escapeHtml(r.route)} ${escapeHtml(r.name)}</h3>
            <p>${(r.stops||[]).length} stops</p>
          </div>
          <div>
            <button class="button secondary edit-route" data-route="${escapeHtml(r.route)}">Edit</button>
            <button class="button route-preview-button" data-route-preview="${escapeHtml(r.route)}">Preview</button>
            <button class="button delete-route" data-route="${escapeHtml(r.route)}">Delete</button>
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
    document.querySelectorAll('[data-route-preview]').forEach(btn => btn.addEventListener('click', e => {
      previewRoute(btn.dataset.routePreview, 'routePreviewMap');
    }));
    document.querySelectorAll('.delete-route').forEach(btn => {
      btn.addEventListener('click', async () => {
        const route = btn.dataset.route;
        if (!confirm(`Delete route ${route}?`)) return;
        const response = await fetch(api + `/routes/${route}`, { method: 'DELETE' });
        if (!response.ok) {
          alert(await response.text());
          return;
        }
        await refreshData();
        renderOperator();
      });
    });
  }

  async function initRoutesAdmin() {
    const save = qs('saveRoute');
    const clear = qs('clearRoute');
    const exportBtn = qs('exportRoutes');
    const importBtn = qs('importRoutesBtn');
    const importArea = qs('importRoutes');
    const routeFile = qs('routeFile');
    const previewRouteFile = qs('previewRouteFile');
    const commitRouteFile = qs('commitRouteFile');
    const routeImportPreview = qs('routeImportPreview');
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
        const replace = state.routes.some(r => r.route === route);
        const response = await fetch(api + `/routes?replace=${replace ? 'true' : 'false'}`, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ route, name, polyline: poly }) });
        if (!response.ok) { alert(await response.text()); return; }
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
    if (exportBtn) {
      exportBtn.addEventListener('click', () => {
        const data = state.routes || [];
        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url; a.download = 'routes.json'; document.body.appendChild(a); a.click(); a.remove();
      });
    }
    async function importPastedRoutes() {
      try {
        const json = JSON.parse(importArea.value);
        if (!Array.isArray(json)) throw new Error('Expected array');
        for (const r of json) {
          const poly = (r.polyline || []).map(p => Array.isArray(p) ? p : [p.latitude, p.longitude]);
          const response = await fetch(api + '/routes?replace=true', { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify({ route: r.route, name: r.name, polyline: poly }) });
          if (!response.ok) throw new Error(await response.text());
        }
        await refreshData();
        renderOperator();
        showToast(`Imported ${json.length} route${json.length === 1 ? '' : 's'}.`);
      } catch (e) {
        alert('Invalid JSON: ' + e.message);
      }
    }
    if (importBtn && importArea) {
      importBtn.addEventListener('click', () => {
        const importIsVisible = importArea.classList.contains('is-visible');
        if (importIsVisible && importArea.value.trim()) {
          importPastedRoutes();
          return;
        }
        importArea.classList.toggle('is-visible');
      });
      importArea.addEventListener('change', async () => {
        if (importArea.value.trim()) await importPastedRoutes();
      });
    }
    async function uploadRouteFile(commit) {
      if (!routeFile || !routeFile.files || !routeFile.files[0]) {
        alert('Choose a GeoJSON, CSV, or GTFS zip file first.');
        return;
      }
      const form = new FormData();
      form.append('file', routeFile.files[0]);
      form.append('commit', commit ? 'true' : 'false');
      form.append('replace', qs('replaceRoutes')?.checked ? 'true' : 'false');
      form.append('simplify_tolerance', '0.00002');
      const response = await fetch(api + '/routes/import', { method: 'POST', body: form });
      const result = await response.json();
      if (!response.ok) {
        routeImportPreview.innerHTML = `<p class="error">${escapeHtml(result.detail || 'Upload failed')}</p>`;
        return;
      }
      routeImportPreview.innerHTML = renderImportResult(result);
      if (commit && result.status === 'committed') {
        await refreshData();
        renderOperator();
      }
    }
    if (previewRouteFile) previewRouteFile.addEventListener('click', () => uploadRouteFile(false));
    if (commitRouteFile) commitRouteFile.addEventListener('click', () => uploadRouteFile(true));
  }

  function renderImportResult(result) {
    const errors = result.errors || [];
    const routes = result.routes || [];
    if (errors.length) {
      return `<p class="error">${errors.map(escapeHtml).join('<br/>')}</p>`;
    }
    return `
      <p>${escapeHtml(result.status)} ${routes.length} route(s) from ${escapeHtml(result.filename || 'upload')}.</p>
      ${routes.slice(0, 5).map(route => `<article><strong>${escapeHtml(route.route)} ${escapeHtml(route.name)}</strong><p>${(route.polyline || []).length} points</p></article>`).join('')}
    `;
  }

  function renderDatabaseStatus() {
    const tables = state.database.tables || {};
    const stats = state.database.stats || {};
    const routeLoads = state.database.route_loads || [];
    const vehicleRoutes = state.database.vehicle_routes || [];
    const alertStatuses = state.database.alert_statuses || [];
    const recentChats = state.database.recent_chats || [];
    const maxSamples = Math.max(1, ...routeLoads.map(row => Number(row.samples || 0)));
    qs("databaseStatus").innerHTML = Object.keys(tables).length
      ? `
        <div class="db-summary-row">
          ${[
            ["Telemetry samples", stats.telemetry_samples ?? tables.telemetry_logs ?? 0],
            ["Active route groups", stats.active_vehicle_routes ?? 0],
            ["Chatbot queries", stats.chat_queries ?? tables.chatbot_queries ?? 0],
            ["Open alerts", stats.open_alerts ?? 0],
          ].map(([label, value]) => `
            <article>
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </article>
          `).join("")}
        </div>
        <div class="db-visual-grid">
          <section>
            <h3>Telemetry by route</h3>
            <div class="db-bars">
              ${routeLoads.length ? routeLoads.map(row => `
                <div class="db-bar-row">
                  <span>${escapeHtml(row.route)}</span>
                  <i data-bar-width="${Math.max(8, (Number(row.samples || 0) / maxSamples) * 100)}"></i>
                  <strong>${escapeHtml(row.samples)}</strong>
                </div>
              `).join("") : `<p class="empty-copy">No telemetry samples saved yet.</p>`}
            </div>
          </section>
          <section>
            <h3>Live route load</h3>
            <div class="db-route-table">
              ${vehicleRoutes.length ? vehicleRoutes.map(row => `
                <article>
                  <span>Route ${escapeHtml(row.route)}</span>
                  <strong>${escapeHtml(row.vehicles)} PUVs</strong>
                  <p>Avg load ${escapeHtml(row.average_occupancy ?? 0)} - crowded ${escapeHtml(row.crowded ?? 0)}</p>
                </article>
              `).join("") : `<p class="empty-copy">No live vehicle states yet.</p>`}
            </div>
          </section>
        </div>
        <div class="db-visual-grid">
          <section>
            <h3>Alert status</h3>
            <div class="db-chip-row">
              ${alertStatuses.length ? alertStatuses.map(row => `<span>${escapeHtml(row.verification_status || "open")} <strong>${escapeHtml(row.count)}</strong></span>`).join("") : `<p class="empty-copy">No alert records.</p>`}
            </div>
          </section>
          <section>
            <h3>Recent chatbot queries</h3>
            <div class="db-chat-list">
              ${recentChats.length ? recentChats.map(row => `
                <article>
                  <strong>${escapeHtml(row.query)}</strong>
                  <p>${escapeHtml(row.answer)}</p>
                </article>
              `).join("") : `<p class="empty-copy">No chatbot history yet.</p>`}
            </div>
          </section>
        </div>
        <details class="db-table-counts">
          <summary>Table counts and database path</summary>
          <div class="db-summary-row compact">
            ${Object.entries(tables).map(([name, count]) => `
              <article>
                <span>${escapeHtml(name)}</span>
                <strong>${count}</strong>
              </article>
            `).join("")}
          </div>
          <p class="db-path">${escapeHtml(state.database.path || "")}</p>
        </details>
      `
      : `<p class="empty-copy">Database has not been initialized.</p>`;
    qs("databaseStatus").querySelectorAll("[data-bar-width]").forEach(bar => {
      bar.style.width = `${bar.dataset.barWidth}%`;
    });
  }

  function renderIncidentLog() {
    qs("incidentLog").innerHTML = state.incidents.length
      ? state.incidents.slice(0, 8).map(incident => `
          <article>
            <div>
              <h3>${escapeHtml(incident.vehicle_id)} - ${escapeHtml(incident.severity).toUpperCase()}</h3>
              <p>${escapeHtml(incident.message)}</p>
              ${incident.resolution_note ? `<small>${escapeHtml(incident.resolution_note)}</small>` : ""}
            </div>
            <span>${escapeHtml((incident.verification_status || (incident.acknowledged ? "verified" : "open")).replace("_", " "))}</span>
          </article>
        `).join("")
      : `<p class="empty-copy">No incident history yet.</p>`;
  }

  async function initOperator() {
    await refreshData();
    renderOperator();
    await initRoutesAdmin();
    initOperatorTabs();
    qs("refreshOperator").addEventListener("click", async () => {
      await refreshData();
      renderOperator();
    });
    const fleetSearch = qs("fleetSearch");
    if (fleetSearch) {
      fleetSearch.addEventListener("input", event => {
        state.operatorFleetQuery = event.target.value.trim();
        renderOperator();
      });
    }
    const routeFilter = qs("fleetRouteFilter");
    if (routeFilter) {
      routeFilter.addEventListener("change", event => {
        state.operatorRouteFilter = event.target.value || "all";
        renderOperator();
      });
    }
    const tierFilter = qs("fleetTierFilter");
    if (tierFilter) {
      tierFilter.addEventListener("change", event => {
        state.operatorTierFilter = event.target.value || "all";
        renderOperator();
      });
    }
    setInterval(async () => {
      await refreshData();
      renderOperator();
    }, 5000);
  }

  function initOperatorTabs() {
    document.querySelectorAll(".ops-tabs button").forEach(button => {
      button.addEventListener("click", () => activateOperatorTab(button.dataset.opsTab));
    });
  }

  function activateOperatorTab(tabId) {
    const target = qs(tabId);
    if (!target) return;
    document.querySelectorAll(".ops-tabs button").forEach(item => item.classList.toggle("active", item.dataset.opsTab === tabId));
    document.querySelectorAll(".ops-tab-panel").forEach(item => item.classList.toggle("active", item.id === tabId));
    setTimeout(() => {
      Object.values(state.maps).forEach(map => {
        try { map.invalidateSize(); } catch (e) {}
      });
    }, 100);
  }

