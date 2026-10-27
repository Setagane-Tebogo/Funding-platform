
import { useState } from "react";
import "./App.css";
import AuthPage from "./AuthPage";
import BusinessProfile from "./BusinessProfile";
import FindFunding from "./FindFunding";
import MyApplications from "./MyApplications";

const menuItems = [
  { label: "Overview", icon: "▦" },
  { label: "Business Profile", icon: "◈" },
  { label: "Find Funding", icon: "⌕" },
  { label: "My Applications", icon: "▤" },
];

function App() {
  const [user, setUser] = useState(() => {
    try {
      return JSON.parse(sessionStorage.getItem("user")) || null;
    } catch {
      return null;
    }
  });

  const [activePage, setActivePage] = useState("Overview");

  function handleLogin(data) {
    setUser({
      id: data.id,
      name: data.name,
      email: data.email,
      role: data.role,
    });
    setActivePage("Overview");
  }

  function handleLogout() {
    sessionStorage.removeItem("token");
    sessionStorage.removeItem("user");
    setUser(null);
    setActivePage("Overview");
  }

  function renderPage() {
    switch (activePage) {
      case "Business Profile":
        return <BusinessProfile />;

      case "Find Funding":
        return <FindFunding />;

      case "My Applications":
        return <MyApplications />;

      default:
        return (
          <>
            <div className="welcome-row">
              <div>
                <p className="eyebrow">ENTREPRENEUR WORKSPACE</p>
                <h1>Turn your idea into opportunity.</h1>
                <p className="subtitle">
                  Manage your business profile and discover funding
                  opportunities for your next stage of growth.
                </p>
              </div>

              <button
                className="primary-button"
                onClick={() => setActivePage("Business Profile")}
              >
                + Complete business profile
              </button>
            </div>

            <div className="stats-grid">
              <div className="stat-card">
                <div className="stat-top">
                  <span>Funding opportunities</span>
                  <span className="stat-icon purple">⌕</span>
                </div>
                <h2>—</h2>
                <p>Opportunities to explore</p>
              </div>

              <div className="stat-card">
                <div className="stat-top">
                  <span>My applications</span>
                  <span className="stat-icon blue">▤</span>
                </div>
                <h2>0</h2>
                <p>Applications submitted</p>
              </div>

              <div className="stat-card">
                <div className="stat-top">
                  <span>Profile completion</span>
                  <span className="stat-icon green">◈</span>
                </div>
                <h2>—</h2>
                <p>Complete your business profile</p>
              </div>
            </div>

            <div className="content-grid">
              <div className="content-panel">
                <h3>Get started</h3>
                <p>Complete these steps to prepare for funding.</p>

                <div className="checklist">
                  <button
                    className="checklist-item"
                    onClick={() => setActivePage("Business Profile")}
                  >
                    <span className="check-circle">1</span>
                    <span className="checklist-text">
                      <strong>Complete your business profile</strong>
                      <small>Tell funders about your business and goals.</small>
                    </span>
                    <span className="check-arrow">→</span>
                  </button>



                  <button
                    className="checklist-item"
                    onClick={() => setActivePage("Find Funding")}
                  >
                    <span className="check-circle">3</span>
                    <span className="checklist-text">
                      <strong>Explore funding opportunities</strong>
                      <small>Find programmes that suit your business.</small>
                    </span>
                    <span className="check-arrow">→</span>
                  </button>
                </div>
              </div>

              <div className="content-panel opportunity-panel">
                <div className="opportunity-icon">✦</div>
                <p className="eyebrow">YOUR NEXT STEP</p>
                <h3>Find the right funding for your business.</h3>
                <p>
                  Complete your profile to help identify programmes that
                  may suit your business needs.
                </p>
                <button
                  className="secondary-button"
                  onClick={() => setActivePage("Find Funding")}
                >
                  Explore funding →
                </button>
              </div>
            </div>

            <footer>
              FundBridge · Helping businesses connect with funding.
            </footer>
          </>
        );
    }
  }

  if (!user) {
    return <AuthPage onLogin={handleLogin} />;
  }

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <img src="/fundbridge-logo.png" alt="FundBridge" className="sidebar-logo" />

        <p className="nav-label">WORKSPACE</p>

        <nav>
          {menuItems.map((item) => (
            <button
              key={item.label}
              className={`nav-item ${
                activePage === item.label ? "active" : ""
              }`}
              onClick={() => setActivePage(item.label)}
            >
              <span className="nav-icon">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>


        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <span className="breadcrumb">Workspace /</span>
            <strong> {activePage}</strong>
          </div>

          <div className="user-menu">
            <div className="avatar">
              {(user.name || user.email || "U")
                .slice(0, 2)
                .toUpperCase()}
            </div>
            <div>
              <strong>{user.name || "Entrepreneur"}</strong>
              <span>{user.email}</span>
            </div>
            <button
              type="button"
              className="logout-button"
              onClick={handleLogout}
            >
              Log out
            </button>
          </div>
        </header>

        <section className="page-content">{renderPage()}</section>
      </main>
    </div>
  );
}

export default App;
