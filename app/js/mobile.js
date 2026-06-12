  async function requestTripSuggestions(query = "") {
    const destination = qs("destinationInput")?.value.trim();
    const origin = qs("originInput")?.value.trim();
    if (!destination && !query) {
      showToast("Enter a destination first.");
      return null;
    }
    if (origin && destination && origin.toLowerCase() === destination.toLowerCase()) {
      showToast("Origin and destination cannot be the same.");
      return null;
    }
    const result = await getJson("/suggestions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildTripPayload(query)),
    });
    syncTripResult(result);
    renderMobile();
    
    if (!state.tripSuggestions.length && typeof showToast === "function") {
      showToast(state.tripMessage || "Unable to find a route.");
    }
    
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
    const mobileRouteTitle = qs("mobileRouteTitle");
    if (mobileRouteTitle) {
      mobileRouteTitle.textContent = state.tripSuggestions[0]
        ? `Best: Route ${state.tripSuggestions[0].route}`
        : selected ? `Nearest: Route ${selected}` : `Select a route`;
    }
    const mapRoute = qs("mapRoute");
    if (mapRoute) {
      mapRoute.innerHTML = selectOptions(selected);
      mapRoute.value = selected;
    }
    updatePlaceDatalists();

    const routeVehicles = selected ? state.vehicles.filter(vehicle => vehicle.route === selected).sort(vehicleSort) : [];
    const best = routeVehicles[0];
    const activeSuggestions = state.tripSuggestions.length ? state.tripSuggestions : null;
    qs("mobileFleet").innerHTML = activeSuggestions
      ? activeSuggestions.map(renderSuggestionCard).join("")
      : routeVehicles.length
      ? routeVehicles.map(renderVehicleCard).join("")
      : selected
      ? `<p class="empty-copy">No live PUVs for Route ${escapeHtml(selected)} yet. The backend simulator will publish the next loop shortly.</p>`
      : (state.tripMessage && !activeSuggestions)
      ? `<p class="empty-copy">${escapeHtml(state.tripMessage || "Unable to find a route for the given trip.")}</p>`
      : `<p class="empty-copy">Please select an origin and destination to see approaching PUVs.</p>`;
    bindVehicleButtons();

    const bestSuggestion = state.tripSuggestions[0];
    if (bestSuggestion) {
      qs("bestVehicleTitle").textContent = `${bestSuggestion.vehicle_id} - Route ${bestSuggestion.route}`;
      let bodyHtml = "";
      if (bestSuggestion.direction === "multi" && bestSuggestion.legs) {
        const l1 = bestSuggestion.legs[0];
        const l2 = bestSuggestion.legs[1];
        bodyHtml = `
          <div class="multi-leg-itinerary">
            <div class="leg">
              <span class="leg-step">1</span>
              <div>
                <strong>${l1.route}</strong>
                <p>Board: ${l1.boarding_stop.name}</p>
                <p>Alight: ${l1.alighting_stop.name}</p>
              </div>
            </div>
            <div class="leg transfer-leg">
              <span class="leg-step">🚶</span>
              <div>
                <strong>Transfer</strong>
                <p>~${Math.round(bestSuggestion.transfer_walk_meters)}m walk</p>
              </div>
            </div>
            <div class="leg">
              <span class="leg-step">2</span>
              <div>
                <strong>${l2.route}</strong>
                <p>Board: ${l2.boarding_stop.name}</p>
                <p>Alight: ${l2.alighting_stop.name}</p>
              </div>
            </div>
          </div>
          <div class="boarding-detail-row"><span>Total ETA</span><strong>${Math.round(Number(bestSuggestion.eta_minutes || 0))} min</strong></div>
          <div class="boarding-detail-row"><span>Total Fare</span><strong>PHP ${bestSuggestion.fare_pesos || "--"}</strong></div>
        `;
      } else {
        bodyHtml = `
          <div class="boarding-detail-row"><span>ETA</span><strong>${Math.round(Number(bestSuggestion.eta_minutes || 0))} min</strong></div>
          <div class="boarding-detail-row"><span>Occupancy</span><strong>${bestSuggestion.occupancy}/${bestSuggestion.capacity}</strong></div>
          <div class="boarding-detail-row"><span>Fare estimate</span><strong>PHP ${bestSuggestion.fare_pesos || "--"}</strong></div>
          <div class="boarding-detail-row"><span>Alternative</span><strong>${state.tripSuggestions[1] ? state.tripSuggestions[1].route_name : 'None available'}</strong></div>
        `;
      }
      qs("bestVehicleBody").innerHTML = bodyHtml;
      qs("ledPill").className = `occupancy-pill ${tierClass(bestSuggestion.tier)}`;
      qs("ledPill").textContent = `Windshield LED: ${tierLabel(bestSuggestion.tier)}`;
      qs("homeEta").textContent = `${Math.round(Number(bestSuggestion.eta_minutes || 0))}m`;
      qs("homeLoad").textContent = `${bestSuggestion.occupancy}/${bestSuggestion.capacity}`;
      qs("homeSafety").textContent = bestSuggestion.status || "active";
    } else if (best) {
        const safeText = best.route_deviation?.anomaly ? "Verify" : "Clear";
        qs("bestVehicleTitle").textContent = `${best.vehicle_id} - ${tierLabel(best.tier)}`;
        qs("bestVehicleBody").innerHTML = `
          <div class="boarding-detail-row"><span>ETA</span><strong>${best.eta_minutes} min</strong></div>
          <div class="boarding-detail-row"><span>Occupancy</span><strong>${best.occupancy}/${best.capacity}</strong></div>
          <div class="boarding-detail-row"><span>Fare estimate</span><strong>--</strong></div>
          <div class="boarding-detail-row"><span>Alternative</span><strong>None selected</strong></div>
        `;
        qs("ledPill").className = `occupancy-pill ${tierClass(best.tier)}`;
        qs("ledPill").textContent = `Windshield LED: ${tierLabel(best.tier)}`;
        qs("homeEta").textContent = `${best.eta_minutes}m`;
        qs("homeLoad").textContent = `${best.occupancy}/${best.capacity}`;
        qs("homeSafety").textContent = safeText;
    } else {
        qs("bestVehicleTitle").textContent = "No route selected";
        qs("bestVehicleBody").innerHTML = "<p>Please select an origin and destination to find the best boarding option.</p>";
        qs("ledPill").className = "occupancy-pill neutral";
        qs("ledPill").textContent = "Awaiting input";
        qs("homeEta").textContent = "--";
        qs("homeLoad").textContent = "--";
        qs("homeSafety").textContent = "--";
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
    bindPlaceSearch("mapOriginInput", "mapOriginSearchResults");
    bindPlaceSearch("mapDestinationInput", "mapDestinationSearchResults");

    const syncInputs = (sourceId, targetId) => {
      const source = qs(sourceId);
      const target = qs(targetId);
      if (source && target) {
        source.addEventListener("input", () => target.value = source.value);
        source.addEventListener("change", () => target.value = source.value);
      }
    };
    syncInputs("originInput", "mapOriginInput");
    syncInputs("mapOriginInput", "originInput");
    syncInputs("destinationInput", "mapDestinationInput");
    syncInputs("mapDestinationInput", "destinationInput");

    const mapFindPuvBtn = qs("mapFindPuvBtn");
    if (mapFindPuvBtn) {
      mapFindPuvBtn.addEventListener("click", async () => {
        await requestTripSuggestions(qs("mapDestinationInput")?.value.trim());
      });
    }

    qs("loginForm").addEventListener("submit", async event => {
      event.preventDefault();
      // Login only collects mobile number; route selection moved to Home tab
      qs("loginScreen").classList.add("hidden");
      qs("appScreen").classList.remove("hidden");
      await refreshData();
      // attempt to detect user location but do not auto-select route on first load
      try {
        if (navigator.geolocation) {
          navigator.geolocation.getCurrentPosition(async pos => {
            state.lastPosition = { latitude: pos.coords.latitude, longitude: pos.coords.longitude };
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
          originInput.value = destinationInput.value;
          destinationInput.value = originValue;
          originInput.dispatchEvent(new Event("input"));
          originInput.dispatchEvent(new Event("change"));
          destinationInput.dispatchEvent(new Event("input"));
          destinationInput.dispatchEvent(new Event("change"));
          qs("originSearchResults")?.classList.add("hidden");
          qs("destinationSearchResults")?.classList.add("hidden");
          if (typeof showToast === "function") showToast("Trip fields swapped.");
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
          refreshData().then(() => renderMobile());
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

