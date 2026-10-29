import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import markerIcon from "leaflet/dist/images/marker-icon.png";
import markerIconRetina from "leaflet/dist/images/marker-icon-2x.png";
import markerShadow from "leaflet/dist/images/marker-shadow.png";
import "leaflet/dist/leaflet.css";
import "./LocationPicker.css";
import { API_BASE_URL as API } from "./apiBase.js";

const DEFAULT_CENTER = [-29.0, 24.0];
let lastDirectGeocodeAt = 0;
const directGeocodeCache = new Map();
L.Icon.Default.mergeOptions({ iconUrl: markerIcon, iconRetinaUrl: markerIconRetina, shadowUrl: markerShadow });

export default function LocationPicker({ value, onChange }) {
  const mapElement = useRef(null);
  const mapRef = useRef(null);
  const markerRef = useRef(null);
  const onChangeRef = useRef(onChange);
  const valueRef = useRef(value);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [mapError, setMapError] = useState("");

  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);
  useEffect(() => { valueRef.current = value; }, [value]);

  useEffect(() => {
    if (!mapElement.current || mapRef.current) return undefined;
    const initialValue = valueRef.current;
    const hasPin = initialValue?.latitude !== "" && initialValue?.longitude !== ""
      && Number.isFinite(Number(initialValue?.latitude)) && Number.isFinite(Number(initialValue?.longitude));
    const start = hasPin ? [Number(initialValue.latitude), Number(initialValue.longitude)] : DEFAULT_CENTER;
    const map = L.map(mapElement.current, { scrollWheelZoom: false }).setView(start, hasPin ? 15 : 5);
    mapRef.current = map;
    const tiles = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      maxZoom: 19,
      attribution: "&copy; OpenStreetMap contributors",
    }).addTo(map);
    tiles.on("tileerror", () => setMapError("Map tiles could not be loaded. Check your connection; you can still use place search."));
    tiles.on("tileload", () => setMapError(""));

    function placePin(latlng, label) {
      if (!markerRef.current) markerRef.current = L.marker(latlng, { draggable: true }).addTo(map);
      else markerRef.current.setLatLng(latlng);
      markerRef.current.off("dragend").on("dragend", (event) => {
        const point = event.target.getLatLng();
        onChangeRef.current({ location: `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`, latitude: point.lat, longitude: point.lng });
      });
      onChangeRef.current({ location: label || `${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`, latitude: latlng.lat, longitude: latlng.lng });
    }
    map.on("click", (event) => { setResults([]); placePin(event.latlng); });
    if (hasPin) placePin({ lat: start[0], lng: start[1] }, initialValue.location);
    const resizeObserver = new ResizeObserver(() => map.invalidateSize());
    resizeObserver.observe(mapElement.current);
    requestAnimationFrame(() => map.invalidateSize());
    return () => { resizeObserver.disconnect(); map.remove(); mapRef.current = null; markerRef.current = null; };
  }, []);

  useEffect(() => {
    const lat = Number(value?.latitude); const lon = Number(value?.longitude);
    if (!mapRef.current || value?.latitude === "" || value?.longitude === "" || !Number.isFinite(lat) || !Number.isFinite(lon)) return;
    mapRef.current.setView([lat, lon], 15);
    if (!markerRef.current) markerRef.current = L.marker([lat, lon], { draggable: true }).addTo(mapRef.current);
    else markerRef.current.setLatLng([lat, lon]);
    markerRef.current.off("dragend").on("dragend", (event) => {
      const point = event.target.getLatLng();
      onChangeRef.current({ location: `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`, latitude: point.lat, longitude: point.lng });
    });
  }, [value?.latitude, value?.longitude, value?.location]);

  async function directPlaceSearch(text) {
    const key = text.trim().toLocaleLowerCase();
    if (directGeocodeCache.has(key)) return directGeocodeCache.get(key);
    const delay = 1000 - (Date.now() - lastDirectGeocodeAt);
    if (delay > 0) await new Promise((resolve) => window.setTimeout(resolve, delay));
    const url = new URL("https://nominatim.openstreetmap.org/search");
    url.searchParams.set("format", "jsonv2"); url.searchParams.set("limit", "5");
    url.searchParams.set("countrycodes", "za"); url.searchParams.set("q", text.trim());
    const contact = import.meta.env.VITE_GEOCODER_CONTACT;
    if (contact) url.searchParams.set("email", contact);
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 15000);
    let response;
    try {
      response = await fetch(url, { headers: { Accept: "application/json" }, signal: controller.signal });
    } finally {
      window.clearTimeout(timeout);
    }
    lastDirectGeocodeAt = Date.now();
    if (!response.ok) throw new Error("Place search is temporarily unavailable. Try again or click the map to set the pin.");
    const rows = await response.json();
    const places = rows.map((row) => ({ id: String(row.place_id), label: row.display_name, latitude: Number(row.lat), longitude: Number(row.lon) }));
    directGeocodeCache.set(key, places);
    return places;
  }

  async function search(event) {
    event.preventDefault();
    const text = query.trim();
    if (text.length < 2) { setMapError("Enter at least two characters to search."); setResults([]); return; }
    setSearching(true); setMapError(""); setResults([]);
    try {
      let data;
      try {
        const token = sessionStorage.getItem("token");
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 12000);
        let response;
        try {
          response = await fetch(`${API}/api/entrepreneur/location-search?q=${encodeURIComponent(text)}`, {
          headers: { Authorization: `Bearer ${token}` },
            signal: controller.signal,
          });
        } finally {
          window.clearTimeout(timeout);
        }
        if (response.ok) data = await response.json();
        else if ([408, 429, 500, 502, 503, 504].includes(response.status)) data = await directPlaceSearch(text);
        else {
          const errorData = await response.json().catch(() => null);
          throw new Error(errorData?.detail || `Place search failed (HTTP ${response.status}).`);
        }
      } catch (apiError) {
        if (apiError instanceof TypeError || apiError.name === "AbortError") data = await directPlaceSearch(text);
        else throw apiError;
      }
      if (!Array.isArray(data) || data.length === 0) throw new Error("No places found in South Africa. Try adding the suburb, town, or province.");
      setResults(data);
    } catch (error) {
      setMapError(error.message || "Place search is unavailable. You can still click the map to choose a point.");
    } finally { setSearching(false); }
  }

  function chooseResult(result) {
    const point = [Number(result.latitude), Number(result.longitude)];
    if (!Number.isFinite(point[0]) || !Number.isFinite(point[1])) { setMapError("This search result has no usable map coordinates."); return; }
    mapRef.current?.setView(point, 16);
    if (!markerRef.current) markerRef.current = L.marker(point, { draggable: true }).addTo(mapRef.current);
    else markerRef.current.setLatLng(point);
    markerRef.current.off("dragend").on("dragend", (event) => {
      const selected = event.target.getLatLng();
      onChangeRef.current({ location: `${selected.lat.toFixed(5)}, ${selected.lng.toFixed(5)}`, latitude: selected.lat, longitude: selected.lng });
    });
    onChange({ location: result.label, latitude: point[0], longitude: point[1] });
    setResults([]); setMapError("");
  }

  return <div className="location-picker">
    <label className="location-search-label" htmlFor="business-location-search">Business location *</label>
    <p className="location-help">Search for an address or place, choose a result, or click the map. Drag the pin to adjust it.</p>
    <div className="location-search">
      <input id="business-location-search" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); search(event); } }} placeholder="Search suburb, town, or street address" autoComplete="street-address" />
      <button type="button" onClick={search} disabled={searching}>{searching ? "Searching…" : "Search places"}</button>
    </div>
    {results.length > 0 && <ul className="location-search-results" aria-label="Place search results">{results.map((result) => <li key={result.id}><button type="button" onClick={() => chooseResult(result)}>{result.label}</button></li>)}</ul>}
    <div ref={mapElement} className="location-map" role="application" aria-label="Interactive map. Click to choose a business location." />
    {value?.location && <p className="selected-location"><strong>Selected:</strong> {value.location} ({Number(value.latitude).toFixed(5)}, {Number(value.longitude).toFixed(5)})</p>}
    {mapError && <p className="location-map-error" role="status">{mapError}</p>}
    <small className="location-map-note">Map and place data © OpenStreetMap contributors. Coverage may be incomplete.</small>
  </div>;
}
