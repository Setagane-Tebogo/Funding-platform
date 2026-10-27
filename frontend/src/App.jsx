import { useEffect, useState } from "react";
import "./App.css";
import AuthPage from "./AuthPage";
import BusinessProfile from "./BusinessProfile";
import FindFunding from "./FindFunding";
import MyApplications from "./MyApplications";
import FunderDashboard from "./FunderDashboard";
import AdminDashboard from "./AdminDashboard";

const menuItems = [
  { label: "Overview", icon: "▦" },
  { label: "Business Profile", icon: "◈" },
  { label: "Find Funding", icon: "⌕" },
  { label: "My Applications", icon: "▤" },
];

function pageHash(page) {
  return `#${page.toLowerCase().replaceAll(" ", "-")}`;
}

function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem("user")) || null;
    } catch {
      return null;
    }
  });
  const [activePage, setActivePage] = useState("Overview");

  useEffect(() => {
    if (!user) return undefined;

    window.history.replaceState(
      { fundbridge: true, page: activePage },
      "",
      window.location.href.split("#")[0] + pageHash(activePage),
    );

    function handleBack(event) {
      if (event.state?.fundbridge) {
        setActivePage(event.state.page || "Overview");
        return;
      }
      window.history.pushState(
        { fundbridge: true, page: "Overview" },
        "",
        window.location.href.split("#")[0] + pageHash("Overview"),
      );
      setActivePage("Overview");
    }

    window.addEventListener("popstate", handleBack);
    return () => window.removeEventListener("popstate", handleBack);
  // The initial history sentinel is installed once per authenticated session.
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [user]);

  function navigate(page) {
    setActivePage(page);
    window.history.pushState(
      { fundbridge: true, page },
      "",
      window.location.href.split("#")[0] + pageHash(page),
    );
  }

  function handleLogin(data) {
    const nextUser = { id: data.id, name: data.name, email: data.email, role: data.role };
    setUser(nextUser);
    window.history.pushState({ fundbridge: true, page: "Overview" }, "", pageHash("Overview"));
    setActivePage("Overview");
  }

  function handleLogout() {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    setUser(null);
    setActivePage("Overview");
    window.history.replaceState({}, "", window.location.pathname);
  }

  function renderPage() {
    if (activePage === "Business Profile") return <BusinessProfile />;
    if (activePage === "Find Funding") return <FindFunding />;
    if (activePage === "My Applications") return <MyApplications />;

    return (
      <div className="dashboard-page">
        <section className="dashboard-hero">
          <div>
            <p className="eyebrow">ENTREPRENEUR DASHBOARD</p>
            <h1>Build your next opportunity.</h1>
            <p className="subtitle">Manage your business profile, understand your numbers, and find funding that fits your growth plan.</p>
          </div>
          <button className="primary-button" onClick={() => navigate("Business Profile")}>Complete your profile <span>→</span></button>
        </section>

        <section className="stats-grid dashboard-stats">
          <div className="stat-card"><div className="stat-top"><span>Funding opportunities</span><span className="stat-icon purple">⌕</span></div><h2>Explore</h2><p>Find programmes matched to your goals</p></div>
          <div className="stat-card"><div className="stat-top"><span>Business analysis</span><span className="stat-icon blue">↗</span></div><h2>Ready</h2><p>Estimate your path to profitability</p></div>
          <div className="stat-card"><div className="stat-top"><span>Applications</span><span className="stat-icon green">▤</span></div><h2>Track</h2><p>Follow every submitted application</p></div>
        </section>

        <section className="dashboard-grid">
          <div className="content-panel dashboard-panel">
            <div className="panel-heading"><div><p className="eyebrow">YOUR WORKSPACE</p><h3>What would you like to do?</h3></div></div>
            <div className="action-grid">
              <button className="action-card" onClick={() => navigate("Business Profile")}><span className="action-icon purple">◈</span><strong>Build your profile</strong><small>Tell funders about your business and funding needs.</small><span className="action-arrow">→</span></button>
              <button className="action-card" onClick={() => navigate("Find Funding")}><span className="action-icon blue">⌕</span><strong>Find funding</strong><small>Explore active programmes and eligibility requirements.</small><span className="action-arrow">→</span></button>
              <button className="action-card" onClick={() => navigate("My Applications")}><span className="action-icon green">▤</span><strong>Track applications</strong><small>Review the funding applications you have submitted.</small><span className="action-arrow">→</span></button>
            </div>
          </div>
          <div className="content-panel insight-panel"><span className="insight-mark">✦</span><p className="eyebrow">FUNDING READINESS</p><h3>Strong proposals start with clear numbers.</h3><p>Complete your profile and run the business analysis to prepare a clearer funding story.</p><button className="secondary-button" onClick={() => navigate("Business Profile")}>Analyse my proposal →</button></div>
        </section>
      </div>
    );
  }

  if (!user) return <AuthPage onLogin={handleLogin} />;
  if (user.role === "FUNDER") return <RolePage user={user} onLogout={handleLogout}><FunderDashboard /></RolePage>;
  if (user.role === "ADMIN") return <RolePage user={user} onLogout={handleLogout}><AdminDashboard /></RolePage>;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <button className="brand brand-button" onClick={() => navigate("Overview")} aria-label="Go to dashboard"><img src="/fundbridge-logo.png" alt="FundBridge" className="sidebar-logo" /></button>
        <p className="nav-label">WORKSPACE</p>
        <nav>{menuItems.map((item) => <button key={item.label} className={`nav-item ${activePage === item.label ? "active" : ""}`} onClick={() => navigate(item.label)}><span className="nav-icon">{item.icon}</span>{item.label}</button>)}</nav>
      </aside>
      <main className="main-content">
        <header className="topbar"><div><span className="breadcrumb">Workspace /</span><strong> {activePage}</strong></div><div className="user-menu"><div className="avatar">{(user.name || user.email || "U").slice(0, 2).toUpperCase()}</div><div><strong>{user.name || "Entrepreneur"}</strong><span>{user.email}</span></div><button type="button" className="logout-button" onClick={handleLogout}>Log out</button></div></header>
        <section className="page-content">{renderPage()}</section>
      </main>
    </div>
  );
}

function RolePage({ user, onLogout, children }) {
  return <div className="app-shell"><main className="main-content"><header className="topbar"><div><span className="breadcrumb">FundBridge /</span><strong> Workspace</strong></div><div className="user-menu"><div className="avatar">{(user.name || user.email).slice(0, 2).toUpperCase()}</div><div><strong>{user.name || user.email}</strong><span>{user.role}</span></div><button type="button" className="logout-button" onClick={onLogout}>Log out</button></div></header><section className="page-content">{children}</section></main></div>
}

export default App;

