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
    mapClusters: {},
    geoWatchId: null,
    lastPosition: null,
    selectedDestination: null,
    selectedVehicleId: null,
    routeQuery: "",
    cityFilter: "all",
    places: [],
    tripSuggestions: [],
    tripMatches: [],
    tripMessage: "",
    originInput: "Current Location",
    destinationInput: "",
    operatorFleetQuery: "",
    operatorRouteFilter: "all",
    operatorTierFilter: "all",
    placeSearchTimers: {},
    chatContext: { route: "", vehicleId: "" },
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

  function showToast(message) {
    let toast = qs("loadsenseToast");
    if (!toast) {
      toast = document.createElement("div");
      toast.id = "loadsenseToast";
      toast.className = "loadsense-toast";
      document.body.appendChild(toast);
    }
    toast.textContent = String(message || "");
    toast.classList.add("show");
    clearTimeout(showToast._timer);
    showToast._timer = setTimeout(() => toast.classList.remove("show"), 2600);
  }

  function cityName(route) {
    return route.city || route.zone || "Philippines";
  }

  function routeStopPoints(route) {
    const points = (route?.stops && route.stops.length ? route.stops : route?.polyline || []);
    return points.filter(isMapCoordinate);
  }

  function routeDistanceMeters(route, origin) {
    if (!origin || !isMapCoordinate(origin)) return Number.POSITIVE_INFINITY;
    const points = routeStopPoints(route);
    if (!points.length) return Number.POSITIVE_INFINITY;
    return points.reduce((best, point) => {
      const distance = haversineMeters(Number(origin.latitude), Number(origin.longitude), Number(point.latitude), Number(point.longitude));
      return Math.min(best, distance);
    }, Number.POSITIVE_INFINITY);
  }

  function sortedRoutesForDisplay(routes) {
    const origin = state.lastPosition;
    return [...routes].sort((left, right) => {
      const leftDistance = routeDistanceMeters(left, origin);
      const rightDistance = routeDistanceMeters(right, origin);
      if (leftDistance !== rightDistance) return leftDistance - rightDistance;
      return `${cityName(left)} ${left.route}`.localeCompare(`${cityName(right)} ${right.route}`);
    });
  }

  function routeSummary(route) {
    const points = routeStopPoints(route);
    const vehicles = state.vehicles.filter(vehicle => vehicle.route === route.route);
    const distance = routeDistanceMeters(route, state.lastPosition);
    return {
      stopCount: points.length,
      vehicleCount: vehicles.length,
      distanceKm: Number.isFinite(distance) ? (distance / 1000).toFixed(1) : null,
      endpoints: route.endpoints || (points.length >= 2 ? [points[0].name, points[points.length - 1].name] : []),
      landmarks: (route.landmarks || []).slice(0, 4),
      vehicles,
    };
  }

  function vehicleSort(a, b) {
    const rank = { green: 0, yellow: 1, red: 2, blinking_red: 3 };
    return (rank[a.tier] ?? 9) - (rank[b.tier] ?? 9) || a.eta_minutes - b.eta_minutes;
  }

  function isMapCoordinate(value) {
    const lat = Number(value?.latitude);
    const lon = Number(value?.longitude);
    return Number.isFinite(lat) && Number.isFinite(lon) && lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180 && !(lat === 0 && lon === 0);
  }

  function toRad(value) {
    return value * Math.PI / 180;
  }

  function haversineMeters(aLat, aLon, bLat, bLon) {
    const radius = 6371000;
    const dLat = toRad(bLat - aLat);
    const dLon = toRad(bLon - aLon);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(toRad(aLat)) * Math.cos(toRad(bLat)) * Math.sin(dLon / 2) ** 2;
    return radius * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  }

  function routePoint(route, ratio) {
    const points = (route?.polyline || []).filter(isMapCoordinate);
    if (!points.length) return null;
    return points[Math.min(points.length - 1, Math.max(0, Math.floor(points.length * ratio)))];
  }

  async function refreshData() {
    const [fleet, routes, alerts, demand, database, incidents, places] = await Promise.all([
      getJson("/fleet"),
      getJson("/routes"),
      getJson("/alerts"),
      getJson("/demand"),
      getJson("/database/status"),
      getJson("/incidents"),
      getJson("/places?limit=300"),
    ]);
    state.vehicles = fleet.vehicles || [];
    state.summary = fleet.summary || {};
    state.routes = routes.routes || [];
    if (state.routes.length && !state.routes.some(route => route.route === state.selectedRoute)) {
      state.selectedRoute = state.routes[0].route;
    }
    state.alerts = alerts.alerts || [];
    state.demand = demand || {};
    state.database = database || {};
    state.incidents = incidents.incidents || [];
    state.places = (places.places && places.places.length ? places.places : buildPlaceOptions());
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

  function buildPlaceOptions() {
    const places = [];
    for (const route of state.routes) {
      const city = route.city || "Philippines";
      for (const stop of route.stops || []) {
        if (isMapCoordinate(stop)) {
          places.push({
            name: stop.name,
            city,
            route: route.route,
            latitude: Number(stop.latitude),
            longitude: Number(stop.longitude),
          });
        }
      }
      const endpoints = route.endpoints || [];
      const firstPoint = (route.polyline || []).find(isMapCoordinate);
      const lastPoint = [...(route.polyline || [])].reverse().find(isMapCoordinate);
      if (endpoints[0] && firstPoint) {
        places.push({ name: endpoints[0], city, route: route.route, latitude: Number(firstPoint.latitude), longitude: Number(firstPoint.longitude) });
      }
      if (endpoints[1] && lastPoint) {
        places.push({ name: endpoints[1], city, route: route.route, latitude: Number(lastPoint.latitude), longitude: Number(lastPoint.longitude) });
      }
    }
    const seen = new Set();
    return places.filter(place => {
      const key = `${place.name.toLowerCase()}-${place.latitude.toFixed(4)}-${place.longitude.toFixed(4)}`;
      if (seen.has(key)) return false;
      seen.add(key);
      return true;
    }).sort((a, b) => `${a.city} ${a.name}`.localeCompare(`${b.city} ${b.name}`));
  }

  function updatePlaceDatalists() {
    const cityFilter = qs("cityFilter");
    if (cityFilter) {
      const cities = ["all", ...new Set(state.routes.map(route => cityName(route)))];
      cityFilter.innerHTML = cities.map(city => `<option value="${escapeHtml(city)}">${escapeHtml(city === "all" ? "All cities" : city)}</option>`).join("");
      if (!cities.includes(state.cityFilter)) state.cityFilter = "all";
      cityFilter.value = state.cityFilter;
    }
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
        const map = L.map(containerId, { zoomControl: true, attributionControl: false }).setView([10.3157, 123.8854], 13);
        L.tileLayer('https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png', {
          maxZoom: 19,
        }).addTo(map);
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
        const latlngs = (route.polyline || []).filter(p => Number(p.latitude) && Number(p.longitude)).map(p => [Number(p.latitude), Number(p.longitude)]);
        if (latlngs.length) {
            const selectedRoute = route.route === state.selectedRoute;
            if (selectedRoute) {
              L.polyline(latlngs, { color: '#ffffff', weight: 12, opacity: 0.95, lineCap: 'round', lineJoin: 'round' }).addTo(layerGroup);
              L.polyline(latlngs, { color: '#0b57d0', weight: 8, opacity: 0.98, lineCap: 'round', lineJoin: 'round' }).addTo(layerGroup);
              L.polyline(latlngs, { color: '#58a6ff', weight: 3, opacity: 0.95, lineCap: 'round', lineJoin: 'round' }).addTo(layerGroup);
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

  function renderSuggestionCard(suggestion) {
    return `
      <article class="vehicle-card suggestion-card">
        <div>
          <h4>${escapeHtml(suggestion.vehicle_id)} <span>Route ${escapeHtml(suggestion.route)}</span></h4>
          <p>${escapeHtml(suggestion.route_name || routeName(suggestion.route))}</p>
          <p>Board: ${escapeHtml(suggestion.boarding_stop?.name || "nearest stop")} - Alight: ${escapeHtml(suggestion.alighting_stop?.name || "destination")}</p>
          <p>${Number(suggestion.distance_km || 0).toFixed(1)} km away - arriving in ~${Math.round(Number(suggestion.eta_minutes || 0))} min - PHP ${escapeHtml(suggestion.fare_pesos || "--")}</p>
        </div>
        <div class="vehicle-card-actions">
          <span class="occupancy-pill ${tierClass(suggestion.tier)}">${tierLabel(suggestion.tier)}</span>
          <button class="mini-action" data-zoom-vehicle="${escapeHtml(suggestion.vehicle_id)}">Zoom</button>
          <button class="mini-action" data-select-route="${escapeHtml(suggestion.route)}">Route</button>
        </div>
      </article>
    `;
  }

  function placeFromInput(value) {
    const normalized = String(value || "").trim().toLowerCase();
    if (!normalized || normalized === "current location" || normalized === "my location") return null;
    return rankedPlaces(normalized, 1)[0] || null;
  }

  function normalizeSearch(value) {
    return String(value || "").toLowerCase().replace(/[^a-z0-9\s]/g, " ").replace(/\s+/g, " ").trim();
  }

  function placeSearchText(place) {
    return normalizeSearch(`${place.name || ""} ${place.city || ""} ${place.route || ""} ${(place.aliases || []).join(" ")}`);
  }

  function rankedPlaces(query, limit = 8) {
    const needle = normalizeSearch(query);
    if (!needle) return [];
    const tokens = needle.split(" ");
    const routeLike = /^(route\s+)?[a-z0-9]{1,4}$/.test(needle);
    return state.places
      .map(place => {
        const haystack = placeSearchText(place);
        let score = 0;
        if (haystack === needle) score = 220;
        else if (haystack.includes(needle)) score = 140;
        else if (tokens.every(token => haystack.includes(token))) score = 95;
        else if (haystack.replaceAll(" ", "").includes(needle.replaceAll(" ", ""))) score = 75;
        score += placeKindBoost(place.kind, routeLike);
        return { place, score };
      })
      .filter(item => item.score > 0)
      .sort((left, right) => right.score - left.score || `${left.place.city} ${left.place.name}`.localeCompare(`${right.place.city} ${right.place.name}`))
      .slice(0, limit)
      .map(item => item.place);
  }

  function mergePlaces(places) {
    if (!Array.isArray(places) || !places.length) return;
    const existing = new Set(state.places.map(place => placeKey(place)));
    for (const place of places) {
      const key = placeKey(place);
      if (existing.has(key)) continue;
      existing.add(key);
      state.places.push(place);
    }
  }

  function placeKey(place) {
    return `${normalizeSearch(place?.name)}-${Number(place?.latitude || 0).toFixed(4)}-${Number(place?.longitude || 0).toFixed(4)}`;
  }

  function placeKindBoost(kind, routeLike) {
    const boosts = {
      city: 70,
      town: 68,
      barangay: 66,
      terminal: 58,
      landmark: 54,
      place: 48,
      stop: 14,
      route: routeLike ? 38 : -45,
    };
    return boosts[kind] ?? 0;
  }

  function renderPlaceResults(inputId, panelId) {
    const input = qs(inputId);
    const panel = qs(panelId);
    if (!input || !panel) return;
    const value = input.value.trim();
    const matches = value ? rankedPlaces(value, 7) : [];
    if (!matches.length) {
      panel.classList.add("hidden");
      panel.innerHTML = "";
      return;
    }
    panel.classList.remove("hidden");
    panel.innerHTML = matches.map(place => `
      <button type="button" data-place-name="${escapeHtml(place.name)}">
        <strong>${escapeHtml(place.name)}</strong>
        <span>${escapeHtml(place.city || "Philippines")}${place.route ? ` - Route ${escapeHtml(place.route)}` : ""}</span>
      </button>
    `).join("");
    panel.querySelectorAll("[data-place-name]").forEach(button => {
      button.addEventListener("click", () => {
        input.value = button.dataset.placeName;
        panel.classList.add("hidden");
        panel.innerHTML = "";
        if (inputId === "destinationInput") {
          const place = placeFromInput(input.value);
          if (place && isMapCoordinate(place)) {
            state.selectedDestination = {
              name: place.name,
              latitude: Number(place.latitude),
              longitude: Number(place.longitude),
            };
            renderDestinationConfirm();
          }
        }
      });
    });
  }

  function bindPlaceSearch(inputId, panelId) {
    const input = qs(inputId);
    if (!input) return;
    input.addEventListener("input", () => {
      renderPlaceResults(inputId, panelId);
      clearTimeout(state.placeSearchTimers[inputId]);
      state.placeSearchTimers[inputId] = setTimeout(async () => {
        const query = input.value.trim();
        if (query.length < 2) return;
        try {
          const result = await getJson(`/places?q=${encodeURIComponent(query)}&limit=12&remote=true`);
          mergePlaces(result.places || []);
          renderPlaceResults(inputId, panelId);
        } catch (error) {
          renderPlaceResults(inputId, panelId);
        }
      }, 280);
    });
    input.addEventListener("focus", () => renderPlaceResults(inputId, panelId));
    input.addEventListener("blur", () => {
      setTimeout(() => qs(panelId)?.classList.add("hidden"), 140);
    });
  }

  function queryNeedsRouteSearch(query, destination) {
    const text = `${query || ""} ${destination || ""}`.toLowerCase();
    return Boolean(destination) || /(get to|go to|reach|route to|going to|towards?|papunta|paingon|padung|pakadto|mapan|llegar|hacia)/i.test(text);
  }

  function queryUsesChatRouteContext(query) {
    const text = String(query || "").toLowerCase();
    return /(that route|this route|current route|selected route|in that route|in this route|explain this route|what is this route|which do i ride|which should i ride|which jeepney do i ride)/.test(text);
  }

  function queryLooksLikeFreshTrip(query) {
    const text = String(query || "").toLowerCase();
    return /(get to|go to|reach|route to|going to|need to go|destination|from|currently located|current location|papunta|paingon|padung|pakadto)/.test(text);
  }

  function buildTripPayload(query = "", options = {}) {
    const originInput = qs("originInput");
    const destinationInput = qs("destinationInput");
    state.originInput = originInput?.value.trim() || "Current Location";
    state.destinationInput = destinationInput?.value.trim() || "";
    const chatMode = options.chat === true;
    const useRouteContext = chatMode && queryUsesChatRouteContext(query);
    const freshTrip = chatMode && queryLooksLikeFreshTrip(query);
    const payloadOrigin = chatMode && freshTrip ? "" : state.originInput;
    const payloadDestination = chatMode ? "" : state.destinationInput;
    const originPlace = placeFromInput(payloadOrigin);
    const destinationPlace = placeFromInput(payloadDestination);
    const dynamicRouteSearch = queryNeedsRouteSearch(query, payloadDestination);
    const payload = {
      route: useRouteContext ? (state.chatContext.route || state.selectedRoute) : (dynamicRouteSearch || chatMode ? "" : state.selectedRoute),
      query,
      origin: payloadOrigin,
      destination: payloadDestination,
      limit: 6,
    };
    if (originPlace) {
      payload.origin_latitude = originPlace.latitude;
      payload.origin_longitude = originPlace.longitude;
    } else if (state.lastPosition && /current location|my location|here/i.test(state.originInput)) {
      payload.origin_latitude = state.lastPosition.latitude;
      payload.origin_longitude = state.lastPosition.longitude;
    }
    if (destinationPlace) {
      payload.destination_latitude = destinationPlace.latitude;
      payload.destination_longitude = destinationPlace.longitude;
    }
    return payload;
  }

  function syncTripResult(result) {
    state.tripSuggestions = result?.suggestions || result?.context || [];
    state.tripMatches = result?.matches || [];
    state.tripMessage = result?.answer || "";
    if (result?.destination && isMapCoordinate(result.destination)) {
      state.selectedDestination = {
        latitude: Number(result.destination.latitude),
        longitude: Number(result.destination.longitude),
        name: result.destination.name,
      };
    }
    const nextRoute = state.tripSuggestions[0]?.route || state.tripMatches[0]?.route;
    if (nextRoute) {
      state.selectedRoute = nextRoute;
    }
    if (nextRoute || state.tripSuggestions[0]?.vehicle_id) {
      state.chatContext.route = nextRoute || state.chatContext.route;
      state.chatContext.vehicleId = state.tripSuggestions[0]?.vehicle_id || state.chatContext.vehicleId;
    }
  }

  function syncChatResult(result) {
    const tripLike = Boolean(result?.destination || (result?.matches || []).length || (result?.context || [])[0]?.boarding_stop);
    if (tripLike) {
      syncTripResult(result);
      return;
    }
    const firstVehicle = (result?.context || []).find(item => item.vehicle_id && item.route);
    if (firstVehicle) {
      state.chatContext.route = firstVehicle.route;
      state.chatContext.vehicleId = firstVehicle.vehicle_id;
    } else if (result?.route && result.route !== "all") {
      state.chatContext.route = result.route;
    }
  }

  function renderBotMessage(result) {
    const firstVehicle = (result?.context || []).find(item => item.vehicle_id && item.route);
    const routeId = firstVehicle?.route || (result?.route && result.route !== "all" ? result.route : state.chatContext.route);
    const actions = [];
    const canZoom = ["boarding", "trip_recommendation"].includes(result?.intent);
    if (canZoom && firstVehicle?.vehicle_id) {
      actions.push(`<button class="mini-action" data-chat-zoom="${escapeHtml(firstVehicle.vehicle_id)}" type="button">Zoom PUV</button>`);
    }
    if (routeId) {
      actions.push(`<button class="mini-action" data-chat-route="${escapeHtml(routeId)}" type="button">Show route</button>`);
    }
    return `
      <div class="message bot">
        <p>${escapeHtml(result?.answer || "I could not answer that yet.")}</p>
        ${actions.length ? `<div class="chat-actions">${actions.join("")}</div>` : ""}
      </div>
    `;
  }

  function bindChatActions(scope) {
    scope.querySelectorAll("[data-chat-zoom]").forEach(button => {
      button.addEventListener("click", () => {
        activateMobileTab("mapTab");
        zoomVehicle(button.dataset.chatZoom);
      });
    });
    scope.querySelectorAll("[data-chat-route]").forEach(button => {
      button.addEventListener("click", () => {
        state.selectedRoute = button.dataset.chatRoute;
        activateMobileTab("mapTab");
        previewRoute(button.dataset.chatRoute, "mobileMap");
      });
    });
  }

  async function requestTripSuggestions(query = "") {
    const destination = qs("destinationInput")?.value.trim();
    if (!destination && !query) {
      showToast("Enter a destination first.");
      return null;
    }
    const result = await getJson("/suggestions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildTripPayload(query)),
    });
    syncTripResult(result);
    renderMobile();
    const map = state.maps.mobileMap;
    const best = state.tripSuggestions[0];
    if (map && state.selectedDestination && typeof L !== "undefined") {
      const points = [[state.selectedDestination.latitude, state.selectedDestination.longitude]];
      if (best && isMapCoordinate({ latitude: best.boarding_stop?.latitude, longitude: best.boarding_stop?.longitude })) {
        points.push([best.boarding_stop.latitude, best.boarding_stop.longitude]);
      }
      try { map.fitBounds(L.latLngBounds(points), { maxZoom: 15, padding: [30, 30] }); } catch (e) {}
    }
    return result;
  }

  function bindVehicleButtons(scope = document) {
    scope.querySelectorAll("[data-zoom-vehicle]").forEach(button => {
      button.addEventListener("click", () => zoomVehicle(button.dataset.zoomVehicle));
    });
    scope.querySelectorAll("[data-select-route]").forEach(button => {
      button.addEventListener("click", () => {
        state.selectedRoute = button.dataset.selectRoute;
        state.tripSuggestions = [];
        renderMobile();
      });
    });
  }

  function initMobileTabs() {
    document.querySelectorAll(".mobile-nav button").forEach(button => {
      button.addEventListener("click", () => activateMobileTab(button.dataset.tab));
    });
  }

  function activateMobileTab(tabId) {
    const target = qs(tabId);
    if (!target) return;
    document.querySelectorAll(".mobile-nav button").forEach(item => item.classList.toggle("active", item.dataset.tab === tabId));
    document.querySelectorAll(".tab-panel").forEach(item => item.classList.toggle("active", item.id === tabId));
    const tripSearch = qs("tripSearchPanel");
    if (tripSearch) {
      tripSearch.classList.toggle("hidden", tabId !== "homeTab");
    }
    setTimeout(() => {
      try { state.maps.mobileMap?.invalidateSize(); } catch (e) {}
    }, 100);
  }

  function renderMobile() {
    const selected = state.selectedRoute;
    qs("mobileRouteTitle").textContent = state.tripSuggestions[0]
      ? `Best: Route ${state.tripSuggestions[0].route}`
      : `Nearest: Route ${selected}`;
    const mapRoute = qs("mapRoute");
    if (mapRoute) {
      mapRoute.innerHTML = selectOptions(selected);
      mapRoute.value = selected;
    }
    updatePlaceDatalists();

    const routeVehicles = state.vehicles.filter(vehicle => vehicle.route === selected).sort(vehicleSort);
    const best = routeVehicles[0] || [...state.vehicles].sort(vehicleSort)[0];
    const activeSuggestions = state.tripSuggestions.length ? state.tripSuggestions : null;
    qs("mobileFleet").innerHTML = activeSuggestions
      ? activeSuggestions.map(renderSuggestionCard).join("")
      : routeVehicles.length
      ? routeVehicles.map(renderVehicleCard).join("")
      : `<p class="empty-copy">No live PUVs for Route ${escapeHtml(selected)} yet. The backend simulator will publish the next loop shortly.</p>`;
    bindVehicleButtons();

    const bestSuggestion = state.tripSuggestions[0];
    if (bestSuggestion) {
      qs("bestVehicleTitle").textContent = `${bestSuggestion.vehicle_id} - Route ${bestSuggestion.route}`;
      qs("bestVehicleBody").textContent = `${state.tripMessage || bestSuggestion.route_name}. Arriving in ~${Math.round(Number(bestSuggestion.eta_minutes || 0))} min from ${Number(bestSuggestion.distance_km || 0).toFixed(1)} km away. Board near ${bestSuggestion.boarding_stop?.name || "nearest stop"}.`;
      qs("ledPill").className = `occupancy-pill ${tierClass(bestSuggestion.tier)}`;
      qs("ledPill").textContent = `Windshield LED: ${tierLabel(bestSuggestion.tier)}`;
      qs("homeEta").textContent = `${Math.round(Number(bestSuggestion.eta_minutes || 0))}m`;
      qs("homeLoad").textContent = `${bestSuggestion.occupancy}/${bestSuggestion.capacity}`;
      qs("homeSafety").textContent = bestSuggestion.status || "active";
    } else if (best) {
        const safeText = best.route_deviation?.anomaly ? "Verify" : "Clear";
        qs("bestVehicleTitle").textContent = `${best.vehicle_id} - ${tierLabel(best.tier)}`;
        qs("bestVehicleBody").textContent = `ETA ${best.eta_minutes} min near Stop ${Number(best.next_stop_id) + 1}. ${best.route_deviation?.anomaly ? "Operator verification is needed before passenger alerting." : "Route is currently within the expected corridor."}`;
        qs("ledPill").className = `occupancy-pill ${tierClass(best.tier)}`;
        qs("ledPill").textContent = `Windshield LED: ${tierLabel(best.tier)}`;
        qs("homeEta").textContent = `${best.eta_minutes}m`;
        qs("homeLoad").textContent = `${best.occupancy}/${best.capacity}`;
        qs("homeSafety").textContent = safeText;
    }

    renderRouteDirectory();
    renderDestinationConfirm();
    drawMap("mobileMap", selected);
    setTimeout(() => fitRoute("mobileMap", selected), 100);
  }

  function renderDestinationConfirm() {
    const panel = qs("destinationConfirm");
    if (!panel) return;
    if (!state.selectedDestination) {
      panel.classList.add("hidden");
      panel.innerHTML = "";
      return;
    }
    const lat = state.selectedDestination.latitude.toFixed(5);
    const lon = state.selectedDestination.longitude.toFixed(5);
    const best = state.tripSuggestions[0] || state.vehicles.filter(v => v.route === state.selectedRoute).sort(vehicleSort)[0];
    panel.classList.remove("hidden");
    panel.innerHTML = `
      <strong>Destination selected</strong>
      <code>${lat}, ${lon}</code>
      <p>${state.tripMessage || (best ? `Suggested PUV ${escapeHtml(best.vehicle_id)} on Route ${escapeHtml(best.route)} - ETA ${escapeHtml(String(best.eta_minutes || 0))} min.` : "Enter a destination and tap Find PUV to search the full route set.")}</p>
      <button id="suggestDestinationPuv" class="button primary" type="button">Find PUV</button>
    `;
    qs("suggestDestinationPuv").addEventListener("click", async () => {
      await requestTripSuggestions(state.destinationInput || state.selectedDestination?.name || "");
    });
  }

  async function askMobileChat(query) {
    const transcript = qs("chatTranscript");
    transcript.insertAdjacentHTML("beforeend", `<div class="message user">${escapeHtml(query)}</div>`);
    const result = await getJson("/chatbot", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildTripPayload(query, { chat: true })),
    });
    syncChatResult(result);
    transcript.insertAdjacentHTML("beforeend", renderBotMessage(result));
    bindChatActions(transcript);
    transcript.scrollTop = transcript.scrollHeight;
    renderMobile();
  }

  async function initMobile() {
    initMobileTabs();
    bindPlaceSearch("originInput", "originSearchResults");
    bindPlaceSearch("destinationInput", "destinationSearchResults");
    qs("loginForm").addEventListener("submit", async event => {
      event.preventDefault();
      // Login only collects mobile number; route selection moved to Home tab
      qs("loginScreen").classList.add("hidden");
      qs("appScreen").classList.remove("hidden");
      await refreshData();
      // attempt to detect user location and auto-select nearest route, then render
      try {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(async pos => {
            const lat = pos.coords.latitude;
            const lon = pos.coords.longitude;
            const nearest = findNearestRoute(lat, lon);
            if (nearest) {
              state.selectedRoute = nearest;
            }
            await refreshData();
            renderMobile();
          }, async () => { await refreshData(); renderMobile(); }, { timeout: 3000 });
        } else {
          await refreshData();
          renderMobile();
        }
      } catch (e) {
        await refreshData();
        renderMobile();
      }
    });
    qs("mapRoute").addEventListener("change", event => {
      state.selectedRoute = event.target.value;
      renderMobile();
    });
    const cityFilter = qs("cityFilter");
    if (cityFilter) {
      cityFilter.addEventListener("change", event => {
        state.cityFilter = event.target.value || "all";
        renderRouteDirectory();
      });
    }
    const findPuvBtn = qs("findPuvBtn");
    if (findPuvBtn) {
      findPuvBtn.addEventListener("click", async () => {
        await requestTripSuggestions();
      });
    }
    const swapTrip = qs("swapTrip");
    if (swapTrip) {
      swapTrip.addEventListener("click", () => {
        const originInput = qs("originInput");
        const destinationInput = qs("destinationInput");
        const originValue = originInput?.value || "";
        if (originInput && destinationInput) {
          originInput.value = destinationInput.value || "Current Location";
          destinationInput.value = originValue === "Current Location" ? "" : originValue;
          showToast("Trip fields swapped.");
        }
      });
    }
    qs("refreshMobile").addEventListener("click", async () => {
      await refreshData();
      renderMobile();
    });
    qs("routeSearch").addEventListener("input", event => {
      state.routeQuery = event.target.value.trim();
      renderRouteDirectory();
    });
    // setup recenter buttons and geolocation watch
    setupRecenterButtons();
    try {
      if (navigator.geolocation) {
        state.geoWatchId = navigator.geolocation.watchPosition(pos => {
          state.lastPosition = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
          const nearest = findNearestRoute(pos.coords.latitude, pos.coords.longitude);
          if (nearest && nearest !== state.selectedRoute) {
            state.selectedRoute = nearest;
            refreshData().then(() => renderMobile());
          }
        }, err => {
          // ignore errors for watch
        }, { enableHighAccuracy: false, maximumAge: 5000, timeout: 5000 });
      }
    } catch (e) {}
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
    qs("forecastBars").innerHTML = rows.length
      ? rows.map(row => `
          <span class="forecast-bar ${forecastLevel(row.expected_load).level}" title="${escapeHtml(row.route)} ${row.expected_load}" style="height:${Math.max(8, (row.expected_load / max) * 100)}%">
            <b>${escapeHtml(row.route)}</b>
          </span>
        `).join("")
      : `<p class="empty-copy">No forecast artifact found.</p>`;
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
            return `
              <article class="route-card clean-route-card${selected}">
                <div class="route-card-head">
                  <div>
                    <h3>${escapeHtml(route.route)} ${escapeHtml(route.name)}</h3>
                    <p>${escapeHtml(route.zone || cityName(route))} - ${summary.stopCount} stops - ${summary.vehicleCount} live PUVs</p>
                  </div>
                  <span class="route-distance">${summary.distanceKm ? `~${summary.distanceKm} km away` : "Near me"}</span>
                </div>
                <div class="route-facts compact">
                  <span>Active PUVs<strong>${summary.vehicleCount}</strong></span>
                  <span>Coverage<strong>${summary.stopCount} stops</strong></span>
                </div>
                <p class="route-landmarks">${escapeHtml((summary.endpoints || []).join(" • "))}</p>
                <p class="route-landmarks muted">${escapeHtml((summary.landmarks || []).join(" • "))}</p>
                <div class="route-actions">
                  <button class="mini-action" data-select-route="${escapeHtml(route.route)}" type="button">Use route</button>
                  <button class="mini-action" data-preview-route="${escapeHtml(route.route)}" type="button">Preview</button>
                </div>
              </article>
            `;
          }).join("")}
        </div>
      </section>
    `).join("");
    container.querySelectorAll("[data-preview-route]").forEach(button => {
      button.addEventListener("click", () => {
        state.selectedRoute = button.dataset.previewRoute;
        activateMobileTab("mapTab");
        previewRoute(button.dataset.previewRoute, "mobileMap");
      });
    });
    container.querySelectorAll("[data-select-route]").forEach(button => {
      button.addEventListener("click", () => {
        state.selectedRoute = button.dataset.selectRoute;
        state.tripSuggestions = [];
        renderMobile();
      });
    });
  }

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
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div>
            <h3>${escapeHtml(r.route)} ${escapeHtml(r.name)}</h3>
            <p>${(r.stops||[]).length} stops</p>
          </div>
          <div>
            <button class="button secondary edit-route" data-route="${escapeHtml(r.route)}">Edit</button>
            <button class="button" style="background:#f0f4f8;color:#0b3550;margin-left:8px" data-route-preview="${escapeHtml(r.route)}">Preview</button>
            <button class="button delete-route" style="background:#f8d7da;color:#7a191b;margin-left:8px" data-route="${escapeHtml(r.route)}">Delete</button>
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
        if (importArea.style.display !== 'none' && importArea.value.trim()) {
          importPastedRoutes();
          return;
        }
        importArea.style.display = importArea.style.display === 'none' ? 'block' : 'none';
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
                  <i style="width:${Math.max(8, (Number(row.samples || 0) / maxSamples) * 100)}%"></i>
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

  async function createAlert(vehicle_id, route, message) {
    try {
      const note = message || prompt(`Describe the incident for ${vehicle_id}`, `${vehicle_id} flagged by operator`);
      if (!note || !confirm(`Create operator incident for ${vehicle_id}?`)) return false;
      const payload = { vehicle_id, route, message: note, severity: 'medium' };
      const response = await fetch(api + '/alerts', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(payload) });
      const result = await response.json();
      if (result.alert) {
        await fetch(api + '/operator-feedback', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ alert_id: result.alert.id, vehicle_id, route, action: `created: ${note}` }),
        });
      }
      await refreshData();
      renderOperator();
      return true;
    } catch (e) {
      console.error(e);
      return false;
    }
  }

  window.LoadSense = { initMobile, initOperator, createAlert, zoomVehicle };
})();
