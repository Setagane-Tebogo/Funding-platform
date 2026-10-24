import { useEffect, useState } from "react";

const API_ROOT = import.meta.env.VITE_API_URL || "http://localhost:8080";

export default function MyApplications() {
  const [applications, setApplications] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => {
    const timer = window.setTimeout(async () => {
      try {
        const response = await fetch(`${API_ROOT}/api/entrepreneur/applications`, { headers: { Authorization: `Bearer ${sessionStorage.getItem("token")}` } });
        const data = await response.json();
        if (!response.ok) throw new Error("Could not load applications.");
        setApplications(data);
      } catch (err) { setError(err.message); }
    }, 0);
    return () => window.clearTimeout(timer);
  }, []);
  return <div className="content-panel"><p className="eyebrow">APPLICATION TRACKING</p><h1>My Applications</h1><p className="subtitle">Track the applications you have submitted to funders.</p>{error && <p className="profile-message error">{error}</p>}{applications.length === 0 && !error && <p>You have not submitted an application yet. Explore funding opportunities to get started.</p>}<div className="programme-grid">{applications.map((application) => <article className="programme-card" key={application.id}><p className="eyebrow">{application.status.replaceAll("_", " ")}</p><h3>{application.programmeName}</h3><p>{application.proposal}</p><small>Submitted {new Date(application.createdAt).toLocaleDateString()}</small></article>)}</div></div>;
}
