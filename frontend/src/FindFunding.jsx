import { useEffect, useState } from "react";

export default function FindFunding() {
  const [programmes, setProgrammes] = useState([]);
  const [industry, setIndustry] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  async function loadProgrammes(selectedIndustry = "") {
    setLoading(true);
    try {
      const path = selectedIndustry
        ? `/industry/${encodeURIComponent(selectedIndustry)}`
        : "/active";
      const response = await fetch(`http://localhost:8080/api/funder/programmes${path}`);
      const data = await response.json();
      if (!response.ok) throw new Error("Could not load funding programmes.");
      setProgrammes(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => loadProgrammes(), 0);
    return () => window.clearTimeout(timer);
  }, []);

  async function apply(programmeId) {
    const proposal = window.prompt("Briefly explain why your business is suitable for this programme:");
    if (!proposal?.trim()) return;
    setMessage("");
    try {
      const response = await fetch("http://localhost:8080/api/entrepreneur/applications", {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${sessionStorage.getItem("token")}` },
        body: JSON.stringify({ programmeId, proposal }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok) throw new Error(typeof result === "string" ? result : "Could not submit application.");
      setMessage("Application submitted successfully. You can track it under My Applications.");
    } catch (err) { setError(err.message); }
  }

  return (
    <div className="content-panel">
      <p className="eyebrow">FUNDING OPPORTUNITIES</p>
      <h1>Find Funding</h1>
      <p className="subtitle">Explore active programmes and compare them with your business needs.</p>
      <div className="funding-filter">
        <select value={industry} onChange={(event) => { setIndustry(event.target.value); loadProgrammes(event.target.value); }}>
          <option value="">All industries</option>
          <option>Technology</option><option>Agriculture</option><option>Manufacturing</option>
          <option>Retail</option><option>Education</option><option>Healthcare</option><option>Tourism</option>
        </select>
      </div>
      {loading && <p>Loading opportunities...</p>}
      {error && <p className="profile-message error">{error}</p>}
      {message && <p className="profile-message success">{message}</p>}
      {!loading && !error && programmes.length === 0 && <p>No active programmes match this filter yet.</p>}
      <div className="programme-grid">
        {programmes.map((programme) => (
          <article className="programme-card" key={programme.id}>
            <p className="eyebrow">{programme.fundingType}</p>
            <h3>{programme.programmeName}</h3>
            <p>{programme.description || "Funding programme for eligible businesses."}</p>
            <strong>R{Number(programme.minimumFunding).toLocaleString()} – R{Number(programme.maximumFunding).toLocaleString()}</strong>
            <small>{programme.industry} · {programme.businessStage} · {programme.location}</small>
            {programme.applicationDeadline && <small>Deadline: {programme.applicationDeadline}</small>}
            <button type="button" className="secondary-button" onClick={() => apply(programme.id)}>Apply to programme</button>
          </article>
        ))}
      </div>
    </div>
  );
}
