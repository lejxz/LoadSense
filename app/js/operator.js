  function renderForecast() {
    const allRows = state.demand.forecast || [];
    const rows = allRows.slice(0, 24);
    const max = Math.max(1, ...rows.map(row => row.expected_load || 0));
    const routeStats = forecastRouteStats(allRows);
    const pressure = routeStats.slice(0, 6);
    const summary = qs("forecastSummary");
    if (summary) {
      summary.innerHTML = pressure.length
        ? pressure.map(item => `
            <article class="forecast-card ${item.level}">
              <span>${escapeHtml(item.route)}</span>
              <strong>${item.peakLoad.toFixed(1)}</strong>
              <p>${escapeHtml(item.routeName)} - peak ${escapeHtml(item.peakTime)} - ${escapeHtml(item.levelLabel)}</p>
            </article>
          `).join("")
        : `<p class="empty-copy">No demand summary available.</p>`;
    }
    const advice = qs("dispatchAdvice");
    if (advice) {
      const actions = buildDispatchAdvice(pressure);
      advice.innerHTML = actions.length
        ? actions.map(item => `
            <article class="dispatch-card ${item.level}">
              <div>
                <h3>${escapeHtml(item.title)}</h3>
                <p>${escapeHtml(item.detail)}</p>
              </div>
              <button class="mini-action" data-demand-route="${escapeHtml(item.route)}" type="button">Show fleet</button>
            </article>
          `).join("")
        : `<p class="empty-copy">Forecast is calm. Keep normal headways and monitor live load.</p>`;
      advice.querySelectorAll("[data-demand-route]").forEach(button => {
        button.addEventListener("click", () => {
          state.operatorRouteFilter = button.dataset.demandRoute;
          activateOperatorTab("opsFleet");
          renderOperator();
        });
      });
    }
    const forecastBars = qs("forecastBars");
    forecastBars.innerHTML = rows.length
      ? rows.map(row => `
          <span class="forecast-bar ${forecastLevel(row.expected_load).level}" title="${escapeHtml(row.route)} ${row.expected_load}" data-bar-height="${Math.max(8, (row.expected_load / max) * 100)}">
            <b>${escapeHtml(row.route)}</b>
          </span>
        `).join("")
      : `<p class="empty-copy">No forecast artifact found.</p>`;
    forecastBars.querySelectorAll("[data-bar-height]").forEach(bar => {
      bar.style.height = `${bar.dataset.barHeight}%`;
    });
    qs("forecastMeta").textContent = rows.length
      ? `${state.demand.model || "forecast"} - generated ${state.demand.generated_at || "from checked-in artifact"}`
      : "";
  }

  function forecastRouteStats(rows) {
    const grouped = rows.reduce((accumulator, row) => {
      const route = row.route || "unknown";
      if (!accumulator[route]) accumulator[route] = [];
      accumulator[route].push(row);
      return accumulator;
    }, {});
    return Object.entries(grouped).map(([route, items]) => {
      const peak = items.reduce((best, row) => Number(row.expected_load || 0) > Number(best.expected_load || 0) ? row : best, items[0]);
      const average = items.reduce((sum, row) => sum + Number(row.expected_load || 0), 0) / Math.max(1, items.length);
      const liveVehicles = state.vehicles.filter(vehicle => vehicle.route === route);
      const liveSeats = liveVehicles.reduce((sum, vehicle) => sum + Math.max(0, Number(vehicle.capacity || 0) - Number(vehicle.occupancy || 0)), 0);
      const level = forecastLevel(Number(peak.expected_load || 0));
      return {
        route,
        routeName: routeName(route),
        peakLoad: Number(peak.expected_load || 0),
        averageLoad: average,
        peakTime: formatHour(peak.timestamp),
        liveVehicles: liveVehicles.length,
        liveSeats,
        level: level.level,
        levelLabel: level.label,
      };
    }).sort((left, right) => right.peakLoad - left.peakLoad);
  }

  function forecastLevel(load) {
    if (load >= 11) return { level: "critical", label: "add capacity" };
    if (load >= 9.5) return { level: "watch", label: "watch headway" };
    return { level: "normal", label: "normal service" };
  }

  function buildDispatchAdvice(stats) {
    return stats
      .filter(item => item.level !== "normal" || item.liveSeats < 8)
      .slice(0, 4)
      .map(item => {
        const scarceSeats = item.liveVehicles ? item.liveSeats < 8 : true;
        const title = item.level === "critical"
          ? `Stage spare PUVs for Route ${item.route}`
          : `Monitor Route ${item.route}`;
        const detail = scarceSeats
          ? `${item.routeName}: forecast peaks at ${item.peakLoad.toFixed(1)} around ${item.peakTime}, with only ${item.liveSeats} visible spare seats now.`
          : `${item.routeName}: forecast peaks at ${item.peakLoad.toFixed(1)} around ${item.peakTime}; keep dispatch spacing tight.`;
        return { route: item.route, level: item.level, title, detail };
      });
  }

  function formatHour(timestamp) {
    if (!timestamp) return "--";
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return "--";
    return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }

  function renderOperator() {
    qs("opVehicleCount").textContent = state.summary.vehicle_count ?? 0;
    qs("opAlertCount").textContent = state.summary.active_alerts ?? 0;
    qs("opAvgLoad").textContent = state.summary.average_occupancy ?? 0;
    qs("opOverloaded").textContent = state.summary.overloaded ?? 0;
    renderOperatorFilters();
    const filteredVehicles = filteredOperatorVehicles();
    qs("operatorFleet").innerHTML = filteredVehicles.length
      ? filteredVehicles.map(vehicle => `
          <article>
            <div>
              <h3>${escapeHtml(vehicle.vehicle_id)}</h3>
              <p>Route ${escapeHtml(vehicle.route)} - ${escapeHtml(routeName(vehicle.route))}</p>
            </div>
            <span>${vehicle.eta_minutes} min</span>
            <span>${vehicle.occupancy}/${vehicle.capacity}</span>
            <span class="occupancy-pill ${tierClass(vehicle.tier)}">${tierLabel(vehicle.tier)}</span>
            <span>${vehicle.route_deviation?.anomaly ? "Verify route" : "On route"}</span>
            <div class="fleet-actions">
              <button class="mini-action" data-zoom-vehicle="${escapeHtml(vehicle.vehicle_id)}">Zoom</button>
              <button class="mini-action" data-alert-vehicle="${escapeHtml(vehicle.vehicle_id)}" data-alert-route="${escapeHtml(vehicle.route)}">Flag</button>
            </div>
          </article>
        `).join("")
      : `<p class="empty-copy">No vehicles match the current filters.</p>`;
    document.querySelectorAll("[data-zoom-vehicle]").forEach(button => {
      button.addEventListener("click", () => zoomVehicle(button.dataset.zoomVehicle));
    });
    document.querySelectorAll("[data-alert-vehicle]").forEach(button => {
      button.addEventListener("click", () => createAlert(button.dataset.alertVehicle, button.dataset.alertRoute));
    });

    qs("operatorAlerts").innerHTML = state.alerts.length
      ? state.alerts.map(renderAlertCard).join("")
      : `<p class="empty-copy">No active operator alerts.</p>`;
    bindAlertActions(qs("operatorAlerts"));
    drawMap("operatorMap");
    renderForecast();
    renderDatabaseStatus();
    renderIncidentLog();
    renderRoutesAdmin();
  }

  function renderAlertCard(alert) {
    const status = alert.verification_status || (alert.acknowledged ? "verified" : "open");
    const statusLabel = status.replace("_", " ");
    return `
      <article class="alert-card ${escapeHtml(alert.severity)} ${escapeHtml(status)}">
        <div>
          <div class="alert-title-row">
            <h3>${escapeHtml(alert.severity).toUpperCase()} - ${escapeHtml(alert.vehicle_id)}</h3>
            <span class="verification-pill ${escapeHtml(status)}">${escapeHtml(statusLabel)}</span>
          </div>
          <p>${escapeHtml(alert.message)}</p>
          <small>Route ${escapeHtml(alert.route)} - ${new Date(alert.timestamp).toLocaleTimeString()}</small>
          <textarea class="verification-note" data-note-for="${escapeHtml(alert.id)}" rows="2" placeholder="Verification note"></textarea>
        </div>
        <div class="verification-actions">
          <button class="mini-action" data-alert-action="verified" data-alert="${escapeHtml(alert.id)}">Confirm</button>
          <button class="mini-action" data-alert-action="false_alarm" data-alert="${escapeHtml(alert.id)}">False alarm</button>
          <button class="mini-action danger" data-alert-action="escalated" data-alert="${escapeHtml(alert.id)}">Escalate</button>
          <button class="mini-action" data-zoom-vehicle="${escapeHtml(alert.vehicle_id)}">Map</button>
        </div>
      </article>
    `;
  }

  function bindAlertActions(scope) {
    if (!scope) return;
    scope.querySelectorAll("[data-alert-action]").forEach(button => {
      button.addEventListener("click", async () => {
        const alertId = button.dataset.alert;
        const note = scope.querySelector(`[data-note-for="${alertId}"]`)?.value.trim() || "";
        await verifyAlert(alertId, button.dataset.alertAction, note);
      });
    });
    scope.querySelectorAll("[data-zoom-vehicle]").forEach(button => {
      button.addEventListener("click", () => zoomVehicle(button.dataset.zoomVehicle));
    });
  }

  async function verifyAlert(alertId, action, note) {
    await getJson(`/alerts/${alertId}/verify`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action, note }),
    });
    await refreshData();
    renderOperator();
  }

  function renderOperatorFilters() {
    const routeFilter = qs("fleetRouteFilter");
    if (routeFilter) {
      const routes = ["all", ...new Set(state.routes.map(route => route.route))];
      routeFilter.innerHTML = routes.map(route => `<option value="${escapeHtml(route)}">${escapeHtml(route === "all" ? "All routes" : route)}</option>`).join("");
      if (!routes.includes(state.operatorRouteFilter)) state.operatorRouteFilter = "all";
      routeFilter.value = state.operatorRouteFilter;
    }
    const tierFilter = qs("fleetTierFilter");
    if (tierFilter) tierFilter.value = state.operatorTierFilter;
    const search = qs("fleetSearch");
    if (search && document.activeElement !== search) search.value = state.operatorFleetQuery;
  }

  function filteredOperatorVehicles() {
    const query = state.operatorFleetQuery.toLowerCase();
    return state.vehicles.filter(vehicle => {
      const route = state.routes.find(item => item.route === vehicle.route);
      const haystack = `${vehicle.vehicle_id} ${vehicle.route} ${route?.name || ""} ${route?.city || ""} ${vehicle.status || ""}`.toLowerCase();
      return (!query || haystack.includes(query))
        && (state.operatorRouteFilter === "all" || vehicle.route === state.operatorRouteFilter)
        && (state.operatorTierFilter === "all" || vehicle.tier === state.operatorTierFilter);
    });
  }

  function renderRouteDirectory() {
    const query = state.routeQuery.toLowerCase();
    const cityFilter = state.cityFilter || "all";
    const matched = state.routes
      .filter(route => cityFilter === "all" || cityName(route) === cityFilter)
      .filter(route => {
        const haystack = `${route.route} ${route.name} ${route.city || ""} ${route.zone || ""} ${(route.landmarks || []).join(" ")}`.toLowerCase();
        return !query || haystack.includes(query);
      })
      .map(route => ({
        ...route,
        summary: routeSummary(route),
      }))
      .sort((left, right) => {
        const leftDistance = routeDistanceMeters(left, state.lastPosition);
        const rightDistance = routeDistanceMeters(right, state.lastPosition);
        if (leftDistance !== rightDistance) return leftDistance - rightDistance;
        return `${cityName(left)} ${left.route}`.localeCompare(`${cityName(right)} ${right.route}`);
      });
    const container = qs("routeList");
    if (!container) return;
    if (!matched.length) {
      container.innerHTML = `<p class="empty-copy">No route matched that search.</p>`;
      return;
    }
    const grouped = matched.reduce((accumulator, route) => {
      const city = cityName(route);
      if (!accumulator[city]) accumulator[city] = [];
      accumulator[city].push(route);
      return accumulator;
    }, {});
    container.innerHTML = Object.entries(grouped).map(([groupName, groupRoutes]) => `
      <section class="route-group">
        <div class="route-group-head">
          <h3>${escapeHtml(groupName)}</h3>
          <span>${groupRoutes.length} route${groupRoutes.length === 1 ? "" : "s"}</span>
        </div>
        <div class="route-group-list">
          ${groupRoutes.map(route => {
            const summary = route.summary;
            const selected = route.route === state.selectedRoute ? " selected" : "";
            const cleanStr = str => {
              let s = String(str);
              if (route.name) s = s.replace(new RegExp(route.name.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&'), "gi"), "");
              if (route.route) s = s.replace(new RegExp(route.route.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\$&'), "gi"), "");
              s = s.trim();
              if (s.startsWith(':') || s.startsWith('-')) s = s.substring(1).trim();
              if (s.endsWith(':') || s.endsWith('-')) s = s.substring(0, s.length - 1).trim();
              return s || str;
            };
            const namedStops = routeStopPoints(route).filter(s => s.name).map(s => cleanStr(s.name));
            let stopsHtml = '';
            if (namedStops.length > 0) {
              stopsHtml = `<ul class="route-stops-list" style="margin: 4px 0 8px 0; padding-left: 20px; font-size: 13px; color: var(--text-muted); display: grid; gap: 4px;">
                ${namedStops.map(n => `<li>${escapeHtml(n)}</li>`).join("")}
              </ul>`;
            } else {
              const cleanEndpoints = (summary.endpoints || []).map(cleanStr);
              const cleanLandmarks = (summary.landmarks || []).map(cleanStr);
              stopsHtml = `<p class="route-landmarks" style="font-size: 13px; margin-bottom: 4px;">${escapeHtml(cleanEndpoints.join(" • "))}</p>
                           <p class="route-landmarks muted" style="font-size: 13px; color: var(--text-muted);">${escapeHtml(cleanLandmarks.join(" • "))}</p>`;
            }
            return `
              <div class="route-card clean-route-card${selected}">
                <div class="route-card-head">
                  <div>
                    <h3>${escapeHtml(route.route)} ${escapeHtml(route.name)}</h3>
                    <p>${escapeHtml(route.zone || cityName(route))} - ${summary.stopCount} stops - ${summary.vehicleCount} live PUVs</p>
                  </div>
                  <span class="route-distance">${summary.distanceKm ? `~${summary.distanceKm} km away` : "Near me"}</span>
                </div>
                <div class="route-card-body" style="margin-top: 12px; display: none; gap: 8px;">
                  ${stopsHtml}
                  <div class="route-actions" style="margin-top: 8px;">
                    <button class="mini-action" data-use-and-preview-route="${escapeHtml(route.route)}" type="button">Use route &amp; show in map</button>
                  </div>
                </div>
                <div style="margin-top: 8px;">
                  <button class="mini-action outline" data-toggle-route="${escapeHtml(route.route)}" type="button" style="width: 100%;">Show route details</button>
                </div>
              </div>
            `;
          }).join("")}
        </div>
      </section>
    `).join("");
    container.querySelectorAll("[data-use-and-preview-route]").forEach(button => {
      button.addEventListener("click", () => {
        const routeId = button.dataset.useAndPreviewRoute;
        state.selectedRoute = routeId;
        state.tripSuggestions = [];
        renderMobile();
        activateMobileTab("mapTab");
        previewRoute(routeId, "mobileMap");
      });
    });
    container.querySelectorAll("[data-toggle-route]").forEach(button => {
      button.addEventListener("click", () => {
        const body = button.closest('.route-card').querySelector('.route-card-body');
        if (body.style.display === 'none') {
          body.style.display = 'grid';
          button.textContent = 'Hide route details';
        } else {
          body.style.display = 'none';
          button.textContent = 'Show route details';
        }
      });
    });
  }
