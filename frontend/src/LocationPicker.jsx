import { useEffect, useRef, useState } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import "./LocationPicker.css";

const API = window.location.hostname === "localhost"
  ? (import.meta.env.VITE_API_URL || "http://localhost:8080")
  : "https://funding-platform-4vyt.onrender.com";
const DEFAULT_CENTER = [-29.0, 24.0];

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

  async function search(event) {
    event.preventDefault();
    const text = query.trim();
    if (text.length < 2) { setMapError("Enter at least two characters to search."); setResults([]); return; }
    setSearching(true); setMapError(""); setResults([]);
    try {
      const token = sessionStorage.getItem("token");
      const response = await fetch(`${API}/api/entrepreneur/location-search?q=${encodeURIComponent(text)}`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || `Place search failed (HTTP ${response.status}).`);
      if (!Array.isArray(data) || data.length === 0) throw new Error("No places found. Try adding the suburb, town, or province.");
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
    <form className="location-search" onSubmit={search}>
      <input id="business-location-search" value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Search suburb, town, or street address" autoComplete="street-address" />
      <button type="submit" disabled={searching}>{searching ? "Searching…" : "Search places"}</button>
    </form>
    {results.length > 0 && <ul className="location-search-results" aria-label="Place search results">{results.map((result) => <li key={result.id}><button type="button" onClick={() => chooseResult(result)}>{result.label}</button></li>)}</ul>}
    <div ref={mapElement} className="location-map" role="application" aria-label="Interactive map. Click to choose a business location." />
    {value?.location && <p className="selected-location"><strong>Selected:</strong> {value.location} ({Number(value.latitude).toFixed(5)}, {Number(value.longitude).toFixed(5)})</p>}
    {mapError && <p className="location-map-error" role="status">{mapError}</p>}
    <small className="location-map-note">Map and place data © OpenStreetMap contributors. Coverage may be incomplete.</small>
  </div>;
}
