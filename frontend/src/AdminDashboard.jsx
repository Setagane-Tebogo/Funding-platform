import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080";
export default function AdminDashboard() {
  const [organisations, setOrganisations] = useState([]);
  const [message, setMessage] = useState("");
  const token = sessionStorage.getItem("token");
  const headers = { Authorization: `Bearer ${token}` };
  async function load() { const response = await fetch(`${API}/api/admin/organisations/pending`, { headers }); if (response.ok) setOrganisations(await response.json()); }
  // load is intentionally stable for this dashboard session.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { const timer = window.setTimeout(load, 0); return () => window.clearTimeout(timer); }, []);
  async function decide(userId, action) { const response = await fetch(`${API}/api/admin/organisations/${userId}/${action}`, { method: "POST", headers }); setMessage(response.ok ? `Organisation ${action}d.` : "Could not update organisation."); load(); }
  return <div className="role-dashboard"><section className="dashboard-hero"><div><p className="eyebrow">ADMINISTRATION</p><h1>Keep FundBridge trusted.</h1><p className="subtitle">Review organisation applications and manage access to the funding network.</p></div></section><section className="content-panel"><div className="panel-heading"><div><p className="eyebrow">PENDING REVIEW</p><h2>Organisation applications</h2></div><span className="admin-count">{organisations.length} pending</span></div>{message && <p className="profile-message success">{message}</p>}{organisations.length === 0 ? <p className="subtitle">There are no organisation applications waiting for review.</p> : <div className="admin-list">{organisations.map((item) => <article className="admin-card" key={item.userId}><div><strong>{item.organisation.organisationName}</strong><p>{item.name} · {item.email}</p><small>{item.organisation.organisationType || "Organisation"} · {item.organisation.location || "Location not supplied"}</small></div><div className="admin-actions"><button className="primary-button" onClick={() => decide(item.userId, "approve")}>Approve</button><button className="danger-button" onClick={() => decide(item.userId, "reject")}>Reject</button></div></article>)}</div>}</section></div>;
}
