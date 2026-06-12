  function renderSuggestionCard(suggestion) {
    if (suggestion.legs) {
      return `
        <article class="vehicle-card suggestion-card">
          <div>
            <h4>Multi-leg Trip</h4>
            <p>${escapeHtml(suggestion.route_name)}</p>
            <p>1. Board <strong>Route ${escapeHtml(suggestion.legs[0].route)}</strong> near ${escapeHtml(suggestion.legs[0].boarding_stop.name)}</p>
            <p>2. Transfer at <strong>${escapeHtml(suggestion.legs[0].alighting_stop.name)}</strong></p>
            <p>3. Take <strong>Route ${escapeHtml(suggestion.legs[1].route)}</strong> to ${escapeHtml(suggestion.legs[1].alighting_stop.name)}</p>
            <p>${Number(suggestion.distance_km || 0).toFixed(1)} km away - arriving in ~${Math.round(Number(suggestion.eta_minutes || 0))} min - PHP ${escapeHtml(suggestion.fare_pesos || "--")}</p>
          </div>
          <div class="vehicle-card-actions">
            <span class="occupancy-pill ${tierClass(suggestion.tier)}">${tierLabel(suggestion.tier)}</span>
            <button class="mini-action" data-select-route="${escapeHtml(suggestion.legs[0].route)}">Leg 1 Route</button>
            <button class="mini-action" data-select-route="${escapeHtml(suggestion.legs[1].route)}">Leg 2 Route</button>
          </div>
        </article>
      `;
    }
    const rName = suggestion.route_name || routeName(suggestion.route);
    const bName = (suggestion.boarding_stop?.name || "nearest stop").replace(rName, "").trim();
    const aName = (suggestion.alighting_stop?.name || "destination").replace(rName, "").trim();
    return `
      <article class="vehicle-card suggestion-card">
        <div class="vehicle-card-content">
          <h4>${escapeHtml(suggestion.vehicle_id)} <span>Route ${escapeHtml(suggestion.route)}</span></h4>
          <p class="route-name">${escapeHtml(rName)}</p>
          <div class="leg-info">
            <div class="leg-stop"><span>Board</span> <strong>${escapeHtml(bName || "nearest stop")}</strong></div>
            <div class="leg-stop"><span>Alight</span> <strong>${escapeHtml(aName || "destination")}</strong></div>
          </div>
          <p class="trip-meta">${Number(suggestion.distance_km || 0).toFixed(1)} km away &bull; arriving in ~${Math.round(Number(suggestion.eta_minutes || 0))} min &bull; PHP ${escapeHtml(suggestion.fare_pesos || "--")}</p>
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
    const isOrigin = inputId === "originInput" || inputId === "mapOriginInput";
    const isDestination = inputId === "destinationInput" || inputId === "mapDestinationInput";
    
    let matches = value ? rankedPlaces(value, isDestination ? 20 : 7) : [];
    if (isDestination) {
      matches = matches.filter(p => p.kind !== "route" && !(p.kind === "stop" && /Checkpoint|Mid-route|Origin|Terminal/i.test(p.name))).slice(0, 7);
    }

    if (!matches.length && !isOrigin) {
      panel.classList.add("hidden");
      panel.innerHTML = "";
      return;
    }
    panel.classList.remove("hidden");
    
    let html = "";
    if (isOrigin) {
      html += `
        <button type="button" data-use-location="true" class="use-location-btn">
          <strong>📍 Use my location</strong>
        </button>
      `;
    }
    
    html += matches.map(place => `
      <button type="button" data-place-name="${escapeHtml(place.name)}">
        <strong>${escapeHtml(place.name)}</strong>
        <span>${escapeHtml(place.city || "Philippines")}${place.route ? ` - Route ${escapeHtml(place.route)}` : ""}</span>
      </button>
    `).join("");
    
    panel.innerHTML = html;

    const useLocBtn = panel.querySelector("[data-use-location]");
    if (useLocBtn) {
      useLocBtn.addEventListener("click", () => {
        input.value = "";
        input.dispatchEvent(new Event("input"));
        input.dispatchEvent(new Event("change"));
        panel.classList.add("hidden");
        panel.innerHTML = "";
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(pos => {
            state.lastPosition = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
            if (typeof renderMobile === "function") renderMobile();
          }, () => {
            if (typeof showToast === "function") showToast("Location access denied.");
          });
        }
      });
    }

    panel.querySelectorAll("[data-place-name]").forEach(button => {
      button.addEventListener("click", () => {
        input.value = button.dataset.placeName;
        panel.classList.add("hidden");
        panel.innerHTML = "";
        if (isDestination) {
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
          if (document.activeElement === input) {
            renderPlaceResults(inputId, panelId);
          }
        } catch (error) {
          if (document.activeElement === input) {
            renderPlaceResults(inputId, panelId);
          }
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

