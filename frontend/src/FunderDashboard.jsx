import { useEffect, useState } from "react";

const API = import.meta.env.VITE_API_URL || "http://localhost:8080";
const empty = { programmeName: "", fundingType: "Grant", minimumFunding: "", maximumFunding: "", industry: "", businessStage: "", location: "", description: "", requirements: "" };

export default function FunderDashboard() {
  const [programmes, setProgrammes] = useState([]);
  const [form, setForm] = useState(empty);
  const [message, setMessage] = useState("");
  const token = sessionStorage.getItem("token");
  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${token}` };
  async function load() { const response = await fetch(`${API}/api/funder/programmes`, { headers }); if (response.ok) setProgrammes(await response.json()); }
  // load is intentionally stable for this dashboard session.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  useEffect(() => { const timer = window.setTimeout(load, 0); return () => window.clearTimeout(timer); }, []);
  function change(event) { setForm({ ...form, [event.target.name]: event.target.value }); }
  async function submit(event) {
    event.preventDefault(); setMessage("");
    const response = await fetch(`${API}/api/funder/programmes`, { method: "POST", headers, body: JSON.stringify({ ...form, minimumFunding: Number(form.minimumFunding), maximumFunding: Number(form.maximumFunding) }) });
    const data = await response.json().catch(() => null);
    if (!response.ok) { setMessage(data?.detail || "Could not create programme."); return; }
    setMessage("Funding programme published."); setForm(empty); load();
  }
  return <div className="role-dashboard"><section className="dashboard-hero"><div><p className="eyebrow">ORGANISATION WORKSPACE</p><h1>Fund the next great business.</h1><p className="subtitle">Create programmes and connect with entrepreneurs who are ready to grow.</p></div></section><div className="role-columns"><section className="content-panel"><p className="eyebrow">PUBLISH OPPORTUNITY</p><h2>Create a funding programme</h2>{message && <p className="profile-message success">{message}</p>}<form className="role-form" onSubmit={submit}>{Object.entries({ programmeName: "Programme name", fundingType: "Funding type", minimumFunding: "Minimum funding", maximumFunding: "Maximum funding", industry: "Industry", businessStage: "Business stage", location: "Location" }).map(([name, label]) => <label key={name}>{label}<input name={name} value={form[name]} onChange={change} required /></label>)}<label>Description<textarea name="description" value={form.description} onChange={change} rows="3" /></label><label>Requirements<textarea name="requirements" value={form.requirements} onChange={change} rows="3" /></label><button className="primary-button" type="submit">Publish programme</button></form></section><section className="content-panel"><p className="eyebrow">YOUR PROGRAMMES</p><h2>{programmes.length} active programme{programmes.length === 1 ? "" : "s"}</h2>{programmes.length === 0 ? <p className="subtitle">Your published programmes will appear here.</p> : <div className="programme-grid">{programmes.map((item) => <article className="programme-card" key={item.id}><strong>{item.programmeName}</strong><small>{item.industry} · {item.businessStage}</small><small>R{Number(item.minimumFunding).toLocaleString()} – R{Number(item.maximumFunding).toLocaleString()}</small></article>)}</div>}</section></div></div>;
}
