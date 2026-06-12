  const api = `${location.origin}/api`;
  const state = {
    vehicles: [],
    routes: [],
    alerts: [],
    demand: {},
    database: {},
    incidents: [],
    selectedRoute: "",
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
    const originCoord = getCoordinate(origin);
    if (!originCoord || !isMapCoordinate(originCoord)) return Number.POSITIVE_INFINITY;
    const points = routeStopPoints(route);
    if (!points.length) return Number.POSITIVE_INFINITY;
    return points.reduce((best, point) => {
      const coord = getCoordinate(point);
      if (!coord) return best;
      const distance = haversineMeters(originCoord.latitude, originCoord.longitude, coord.latitude, coord.longitude);
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

  function getCoordinate(value) {
    if (!value) return null;
    if (Array.isArray(value)) return { latitude: Number(value[0]), longitude: Number(value[1]) };
    const lat = Number(value.latitude);
    const lon = Number(value.longitude);
    if (Number.isFinite(lat) && Number.isFinite(lon)) return { latitude: lat, longitude: lon };
    return null;
  }

  function isMapCoordinate(value) {
    const coord = getCoordinate(value);
    if (!coord) return false;
    const { latitude: lat, longitude: lon } = coord;
    return lat >= -90 && lat <= 90 && lon >= -180 && lon <= 180 && !(lat === 0 && lon === 0);
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

