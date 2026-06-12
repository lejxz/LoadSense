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
    if (state.selectedRoute !== "" && state.routes.length && !state.routes.some(route => route.route === state.selectedRoute)) {
      state.selectedRoute = "";
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
    const options = state.routes.map(route => {
      const attr = route.route === selected ? " selected" : "";
      return `<option value="${escapeHtml(route.route)}"${attr}>${escapeHtml(route.route)} ${escapeHtml(route.name)}</option>`;
    }).join("");
    return `<option value=""${!selected ? " selected" : ""}>None</option>` + options;
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
        const coord = getCoordinate(firstPoint);
        places.push({ name: endpoints[0], city, route: route.route, latitude: coord.latitude, longitude: coord.longitude });
      }
      if (endpoints[1] && lastPoint) {
        const coord = getCoordinate(lastPoint);
        places.push({ name: endpoints[1], city, route: route.route, latitude: coord.latitude, longitude: coord.longitude });
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
    const points = routes.flatMap(route => route.polyline || []).map(getCoordinate).filter(Boolean);
    if (!points.length) {
      return { minLat: 14.598, maxLat: 14.602, minLon: 120.983, maxLon: 120.988 };
    }
    const lats = points.map(point => point.latitude);
    const lons = points.map(point => point.longitude);
    return {
      minLat: Math.min(...lats),
      maxLat: Math.max(...lats),
      minLon: Math.min(...lons),
      maxLon: Math.max(...lons),
    };
  }

  function project(point, bounds) {
    const coord = getCoordinate(point);
    if (!coord) return { x: 50, y: 50 };
    const latRange = Math.max(0.0001, bounds.maxLat - bounds.minLat);
    const lonRange = Math.max(0.0001, bounds.maxLon - bounds.minLon);
    return {
      x: 8 + ((coord.longitude - bounds.minLon) / lonRange) * 84,
      y: 88 - ((coord.latitude - bounds.minLat) / latRange) * 76,
    };
  }

