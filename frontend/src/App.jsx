import { useEffect, useState } from "react";
import "./App.css";
import AuthPage from "./AuthPage";
import BusinessProfile from "./BusinessProfile";
import FindFunding from "./FindFunding";
import MyApplications from "./MyApplications";
import ChatPanel from "./ChatPanel";
import FunderDashboard from "./FunderDashboard";
import AdminDashboard from "./AdminDashboard";
import ProfilePage from "./ProfilePage";

const menuItems = [
  { label: "Overview", icon: "overview" },
  { label: "Business Profile", icon: "business" },
  { label: "Find Funding", icon: "funding" },
  { label: "My Applications", icon: "applications" },
  { label: "Messages", icon: "messages" },
  { label: "Profile", icon: "profile" },
];

const PROFILE_API = window.location.hostname === "localhost" ? (import.meta.env.VITE_API_URL || "http://localhost:8080") : "https://funding-platform-4vyt.onrender.com";

function NavigationIcon({ name }) {
  const paths = {
    overview: <><path d="m3.5 10 8.5-7 8.5 7" /><path d="M5.5 9v11h13V9M9.5 20v-6h5v6" /></>,
    business: <><rect x="4" y="6" width="16" height="14" rx="1.5" /><path d="M9 6V4h6v2M4 11h16M10 11v2h4v-2" /></>,
    funding: <><circle cx="10.8" cy="10.8" r="6.3" /><path d="m15.4 15.4 5 5M8.5 10.8h4.6M10.8 8.5v4.6" /></>,
    applications: <><path d="M7 4.5h8l4 4V20H7z" /><path d="M15 4.5V9h4M10 13h6M10 16.5h6M4 8v14h12" /></>,
    messages: <><path d="M20 11.5a7.5 7.5 0 0 1-7.5 7.5 8 8 0 0 1-3.5-.8L4 20l1.5-4A7.5 7.5 0 1 1 20 11.5Z" /><path d="M8.5 11.5h.01M12.5 11.5h.01M16.5 11.5h.01" strokeWidth="2.5" /></>,
    profile: <><circle cx="12" cy="8" r="3.5" /><path d="M5 20a7 7 0 0 1 14 0" /></>,
  };

  return <svg className="nav-icon-svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

function pageHash(page) {
  return `#${page.toLowerCase().replaceAll(" ", "-")}`;
}

function pageFromHash() {
  const hash = window.location.hash.replace(/^#/, "");
  const page = menuItems.find((item) => item.label.toLowerCase().replaceAll(" ", "-") === hash);
  return page?.label || "Overview";
}

function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem("user")) || null;
    } catch {
      return null;
    }
  });
  const [activePage, setActivePage] = useState(pageFromHash);
  const [menuOpen, setMenuOpen] = useState(false);
  const [accountProfile, setAccountProfile] = useState(null);

  useEffect(() => {
    if (!user) return undefined;
    fetch(`${PROFILE_API}/api/profile`, { headers: { Authorization: `Bearer ${sessionStorage.getItem("token")}` } }).then((response) => response.ok ? response.json() : null).then((profile) => { if (profile) setAccountProfile(profile); }).catch(() => undefined);
    return undefined;
  }, [user]);

  useEffect(() => {
    function refreshProfile(event) { if (event.detail) setAccountProfile(event.detail); }
    window.addEventListener("fundbridge-profile-updated", refreshProfile);
    return () => window.removeEventListener("fundbridge-profile-updated", refreshProfile);
  }, []);

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
    setMenuOpen(false);
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
    if (activePage === "Messages") return <ChatPanel onProfile={() => navigate("Profile")} />;
    if (activePage === "Profile") return <ProfilePage />;

    const firstName = (accountProfile?.name || user.name || "there").trim().split(/\s+/)[0];

    return (
      <div className="dashboard-page">
        <section className="dashboard-welcome">
          <div className="dashboard-welcome-copy">
            <h1>Welcome back, {firstName}.</h1>
            <p>Manage your business profile, find funding, and keep track of applications.</p>
          </div>
          <button className="primary-button" onClick={() => navigate("Find Funding")}>Find funding</button>
        </section>

        <section className="dashboard-steps" aria-labelledby="dashboard-steps-title">
          <div className="dashboard-section-heading">
            <div>
              <h2 id="dashboard-steps-title">Quick links</h2>
            </div>
          </div>
          <div className="dashboard-action-list">
            <button className="dashboard-step" onClick={() => navigate("Business Profile")}>
              <span className="dashboard-step-copy"><strong>Business profile</strong><small>Update your business details and funding needs.</small></span>
              <span className="dashboard-step-arrow" aria-hidden="true">›</span>
            </button>
            <button className="dashboard-step" onClick={() => navigate("Find Funding")}>
              <span className="dashboard-step-copy"><strong>Funding opportunities</strong><small>Browse programmes and review eligibility requirements.</small></span>
              <span className="dashboard-step-arrow" aria-hidden="true">›</span>
            </button>
            <button className="dashboard-step" onClick={() => navigate("My Applications")}>
              <span className="dashboard-step-copy"><strong>My applications</strong><small>Review the applications you’ve submitted.</small></span>
              <span className="dashboard-step-arrow" aria-hidden="true">›</span>
            </button>
          </div>
        </section>
      </div>
    );
  }

  if (!user) return <AuthPage onLogin={handleLogin} />;
  if (user.role === "FUNDER") return <RolePage user={user} profile={accountProfile} onLogout={handleLogout}>{({ view, onViewChange }) => <FunderDashboard view={view} onViewChange={onViewChange} />}</RolePage>;
  if (user.role === "ADMIN") return <RolePage user={user} profile={accountProfile} onLogout={handleLogout}>{({ view, onViewChange }) => <AdminDashboard view={view} onViewChange={onViewChange} />}</RolePage>;

  return (
    <div className="app-shell">
      {menuOpen && <button type="button" className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <button className="brand brand-button" onClick={() => navigate("Overview")} aria-label="Go to dashboard"><img src="/fundbridge-logo-transparent.png" alt="FundBridge" className="sidebar-logo" /></button>
        <p className="nav-label">Workspace</p>
        <nav>{menuItems.map((item) => <button key={item.label} className={`nav-item ${activePage === item.label ? "active" : ""}`} onClick={() => navigate(item.label)}><span className="nav-icon"><NavigationIcon name={item.icon} /></span>{item.label}</button>)}</nav>
      </aside>
      <main className="main-content">
        <header className="topbar"><div className="topbar-title"><button type="button" className="menu-toggle" aria-label={menuOpen ? "Close navigation" : "Open navigation"} onClick={() => setMenuOpen((open) => !open)}><span></span><span></span><span></span></button><div><span className="breadcrumb">Workspace /</span><strong> {activePage}</strong></div></div><div className="user-menu"><button type="button" className="profile-top-button" onClick={() => navigate("Profile")}><div className="avatar">{accountProfile?.avatar ? <img src={accountProfile.avatar} alt="Profile" /> : (user.name || user.email || "U").slice(0, 2).toUpperCase()}</div><span><strong>{accountProfile?.name || user.name || "Entrepreneur"}</strong><small>{user.email}</small></span></button><button type="button" className="logout-button" onClick={handleLogout}>Log out</button></div></header>
        <section className="page-content">{renderPage()}</section>
      </main>
    </div>
  );
}

function RolePage({ user, profile, onLogout, children }) {
  const [showProfile, setShowProfile] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);
  const navigationItems = user.role === "ADMIN"
    ? [
      { view: "overview", label: "Overview", icon: "overview" },
      { view: "approvals", label: "Approvals", icon: "applications" },
      { view: "programmes", label: "Programmes", icon: "funding" },
      { view: "applications", label: "Applications", icon: "applications" },
      { view: "users", label: "Users", icon: "profile" },
    ]
    : [
      { view: "create", label: "Create programme", icon: "funding" },
      { view: "programmes", label: "Programmes", icon: "funding" },
      { view: "applications", label: "Applications", icon: "applications" },
      { view: "proposals", label: "Saved proposals", icon: "business" },
      { view: "messages", label: "Messages", icon: "messages" },
      { view: "profile", label: "My profile", icon: "profile" },
    ];
  const defaultView = user.role === "ADMIN" ? "overview" : "create";
  const [view, setView] = useState(() => {
    const prefix = user.role === "ADMIN" ? "#admin-" : "#funder-";
    const initialView = window.location.hash.startsWith(prefix) ? window.location.hash.slice(prefix.length) : defaultView;
    return navigationItems.some((item) => item.view === initialView) ? initialView : defaultView;
  });
  const activeItem = navigationItems.find((item) => item.view === view);

  function navigate(viewName) {
    setView(viewName);
    setMenuOpen(false);
    setShowProfile(false);
    const prefix = user.role === "ADMIN" ? "admin" : "funder";
    window.history.replaceState({ fundbridge: true, page: viewName }, "", `#${prefix}-${viewName}`);
  }

  const dashboard = typeof children === "function"
    ? children({ view, onViewChange: navigate })
    : children;

  return (
    <div className="app-shell">
      {menuOpen && <button type="button" className="sidebar-backdrop" aria-label="Close navigation" onClick={() => setMenuOpen(false)} />}
      <aside className={`sidebar ${menuOpen ? "open" : ""}`}>
        <button className="brand brand-button" onClick={() => navigate(defaultView)} aria-label="Go to dashboard">
          <img src="/fundbridge-logo-transparent.png" alt="FundBridge" className="sidebar-logo" />
        </button>
        <p className="nav-label">{user.role === "ADMIN" ? "Administration" : "Organisation workspace"}</p>
        <nav>
          {navigationItems.map((item) => (
            <button
              key={item.view}
              className={`nav-item ${view === item.view && !showProfile ? "active" : ""}`}
              onClick={() => navigate(item.view)}
            >
              <span className="nav-icon"><NavigationIcon name={item.icon} /></span>
              {item.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-bottom">
          <span className="help-icon" aria-hidden="true">?</span>
          <div><strong>Need a hand?</strong><p>We’re here to help.</p></div>
        </div>
      </aside>
      <main className="main-content">
        <header className="topbar">
          <div className="topbar-title">
            <button type="button" className="menu-toggle" aria-label={menuOpen ? "Close navigation" : "Open navigation"} onClick={() => setMenuOpen((open) => !open)}>
              <span></span><span></span><span></span>
            </button>
            <div><span className="breadcrumb">Workspace /</span><strong> {showProfile ? "My profile" : activeItem?.label}</strong></div>
          </div>
          <div className="user-menu">
            <button type="button" className="profile-top-button" onClick={() => { setShowProfile(true); setMenuOpen(false); }}>
              <div className="avatar">{profile?.avatar ? <img src={profile.avatar} alt="Profile" /> : (profile?.name || user.name || user.email).slice(0, 2).toUpperCase()}</div>
              <span><strong>{profile?.name || user.name || user.email}</strong><small>{user.role}</small></span>
            </button>
            <button type="button" className="logout-button" onClick={onLogout}>Log out</button>
          </div>
        </header>
        <section className="page-content">{showProfile ? <ProfilePage /> : dashboard}</section>
      </main>
    </div>
  );
}

export default App;
