import { useEffect, useRef, useState } from "react";

const DEFAULT_CENTER = [-29.0, 24.0];
let leafletPromise;
function loadLeaflet() {
  if (window.L) return Promise.resolve(window.L);
  if (!leafletPromise) leafletPromise = new Promise((resolve, reject) => {
    if (!document.querySelector("link[data-leaflet]")) { const link = document.createElement("link"); link.rel = "stylesheet"; link.href = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"; link.dataset.leaflet = "true"; document.head.appendChild(link); }
    const script = document.createElement("script"); script.src = "https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"; script.async = true; script.onload = () => resolve(window.L); script.onerror = () => reject(new Error("Map library could not be loaded.")); document.head.appendChild(script);
  });
  return leafletPromise;
}

export default function LocationPicker({ value, onChange }) {
  const mapElement = useRef(null); const mapRef = useRef(null); const markerRef = useRef(null); const onChangeRef = useRef(onChange);
  const [query, setQuery] = useState(""); const [searching, setSearching] = useState(false); const [mapError, setMapError] = useState("");
  useEffect(() => { onChangeRef.current = onChange; }, [onChange]);
  useEffect(() => {
    let disposed = false;
    loadLeaflet().then((L) => {
      if (disposed || !mapElement.current || mapRef.current) return;
      const initial = value?.latitude != null && value?.longitude != null ? [Number(value.latitude), Number(value.longitude)] : DEFAULT_CENTER;
      const map = L.map(mapElement.current).setView(initial, value?.latitude != null ? 15 : 5); mapRef.current = map;
      L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", { maxZoom: 19, attribution: "&copy; OpenStreetMap contributors" }).addTo(map);
      function setPin(latlng, label) {
        if (!markerRef.current) markerRef.current = L.marker(latlng, { draggable: true }).addTo(map); else markerRef.current.setLatLng(latlng);
        markerRef.current.off("dragend").on("dragend", (event) => setPin(event.target.getLatLng(), label));
        const current = onChangeRef.current; current({ location: label || `${latlng.lat.toFixed(5)}, ${latlng.lng.toFixed(5)}`, latitude: latlng.lat, longitude: latlng.lng });
      }
      map.on("click", (event) => setPin(event.latlng));
      if (value?.latitude != null && value?.longitude != null) setPin({ lat: Number(value.latitude), lng: Number(value.longitude) }, value.location);
    }).catch((error) => { if (!disposed) setMapError(error.message); });
    return () => { disposed = true; if (mapRef.current) { mapRef.current.remove(); mapRef.current = null; markerRef.current = null; } };
  }, []);
  useEffect(() => {
    const lat = Number(value?.latitude); const lon = Number(value?.longitude);
    if (mapRef.current && Number.isFinite(lat) && Number.isFinite(lon) && value?.latitude !== "" && value?.longitude !== "") {
      mapRef.current.setView([lat, lon], 15);
      if (window.L) {
        if (!markerRef.current) markerRef.current = window.L.marker([lat, lon], { draggable: true }).addTo(mapRef.current);
        else markerRef.current.setLatLng([lat, lon]);
        markerRef.current.off("dragend").on("dragend", (event) => { const point = event.target.getLatLng(); onChangeRef.current({ location: value.location || `${point.lat.toFixed(5)}, ${point.lng.toFixed(5)}`, latitude: point.lat, longitude: point.lng }); });
      }
    }
  }, [value?.latitude, value?.longitude]);
  async function search(event) {
    event.preventDefault(); if (!query.trim()) return; setSearching(true); setMapError("");
    try {
      const response = await fetch(`https://nominatim.openstreetmap.org/search?format=jsonv2&limit=1&q=${encodeURIComponent(query.trim())}`, { headers: { Accept: "application/json" } });
      if (!response.ok) throw new Error("Location search is temporarily unavailable. You can still click the map to place a pin.");
      const results = await response.json(); if (!results.length) throw new Error("No matching place found. Try a nearby suburb, town, or street.");
      const result = results[0]; const latlng = { lat: Number(result.lat), lng: Number(result.lon) }; mapRef.current?.setView(latlng, 15);
      if (mapRef.current && window.L) {
        if (!markerRef.current) markerRef.current = window.L.marker(latlng, { draggable: true }).addTo(mapRef.current); else markerRef.current.setLatLng(latlng);
        markerRef.current.off("dragend").on("dragend", (event) => { const point = event.target.getLatLng(); onChangeRef.current({ location: result.display_name, latitude: point.lat, longitude: point.lng }); });
      }
      onChange({ location: result.display_name, latitude: latlng.lat, longitude: latlng.lng });
    } catch (error) { setMapError(error.message || "Could not search for that place."); } finally { setSearching(false); }
  }
  return <div className="location-picker">
    <label className="location-search-label">Find a place <span>Search once, or click the map to place the pin.</span></label>
    <form className="location-search" onSubmit={search}><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Suburb, town, or street address" aria-label="Search for a business location" /><button type="submit" disabled={searching}>{searching ? "Searching…" : "Find on map"}</button></form>
    <div ref={mapElement} className="location-map" role="application" aria-label="Interactive map. Click to select a business location." />
    {value?.location && <p className="selected-location"><strong>Selected:</strong> {value.location} ({Number(value.latitude).toFixed(5)}, {Number(value.longitude).toFixed(5)})</p>}
    {mapError && <p className="location-map-error" role="status">{mapError}</p>}
    <small className="location-map-note">Map tiles and place search © OpenStreetMap contributors. Map data may be incomplete.</small>
  </div>;
}
