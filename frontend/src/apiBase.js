const PRODUCTION_API = "https://funding-platform-4vyt.onrender.com";

function isLoopbackHost(hostname) {
  const host = hostname.replace(/^\[|\]$/g, "").toLowerCase();
  return host === "localhost" || host.endsWith(".localhost") || host === "::1" || /^127(?:\.\d{1,3}){3}$/.test(host);
}

const configuredApi = import.meta.env.VITE_API_URL?.trim().replace(/\/+$/, "");
const hostname = window.location.hostname.replace(/^\[|\]$/g, "");

// Keep local Vite sessions pointed at the local API even when opened with
// 127.0.0.1 or a *.localhost alias. Deployments can set VITE_API_URL explicitly.
export const API_BASE_URL = configuredApi || (isLoopbackHost(hostname)
  ? `http://${hostname.includes(":") ? `[${hostname}]` : hostname}:8080`
  : PRODUCTION_API);
