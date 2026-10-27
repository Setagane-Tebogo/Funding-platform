
import { useState } from "react";
import "./AuthPage.css";

const API_URL = `${import.meta.env.VITE_API_URL || (window.location.hostname === "localhost" ? "http://localhost:8080" : "https://funding-platform-4vyt.onrender.com")}/api/auth`;

export default function AuthPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [accountType, setAccountType] = useState("ENTREPRENEUR");
  const [organisationName, setOrganisationName] = useState("");
  const [organisationType, setOrganisationType] = useState("");
  const [location, setLocation] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  function changeMode(nextMode) {
    setMode(nextMode);
    setError("");
    setSuccess("");
    setPassword("");
    setConfirmPassword("");
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (mode === "register" && password !== confirmPassword) {
      setError("Your passwords do not match.");
      return;
    }

    if (password.length < 8) {
      setError("Your password must contain at least 8 characters.");
      return;
    }

    setLoading(true);

    try {
      const isRegistering = mode === "register";

      const response = await fetch(
        `${API_URL}/${isRegistering ? "register" : "login"}`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(
            isRegistering
              ? { name: name.trim(), email: email.trim(), password, accountType, organisationName: organisationName.trim(), organisationType, location: location.trim() }
              : { email: email.trim(), password }
          ),
        }
      );

      const data = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          typeof data === "string"
            ? data
            : data?.detail ||
              data?.message ||
              data?.error ||
              `Request failed (HTTP ${response.status}).`
        );
      }

      if (isRegistering) {
        setSuccess(data?.pendingApproval ? "Registration submitted. Please wait for an administrator to approve your organisation before you try to log in." : "Account created successfully. You can now log in.");
        setMode("login");
        setPassword("");
        setConfirmPassword("");
        return;
      }

      if (!data?.token) {
        throw new Error(
          "Login succeeded, but the response did not contain a token. Check your backend login response."
        );
      }

      // Keep the token for this browser tab's session.
      sessionStorage.setItem("token", data.token);
      sessionStorage.setItem("user", JSON.stringify({
        id: data.id,
        name: data.name,
        email: data.email,
        role: data.role,
      }));

      onLogin(data);
    } catch (err) {
      setError(
        err.message ||
          "Could not connect to the server. Make sure your backend is running."
      );
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-brand-panel">
        <div className="auth-brand">
          <img src="/fundbridge-logo.png" alt="FundBridge" className="auth-logo" />
          
        </div>

        <div className="auth-brand-content">
          <p className="auth-eyebrow">FUNDING STARTS HERE</p>
          <h1>Great businesses deserve the chance to grow.</h1>
          <p>
            Connect your business ambitions with funding opportunities
            designed to help you move forward.
          </p>

          <div className="auth-feature">
            <span>✓</span>
            <div>
              <strong>One business profile</strong>
              <p>Present your business and funding needs.</p>
            </div>
          </div>

          <div className="auth-feature">
            <span>✓</span>
            <div>
              <strong>Funding opportunities</strong>
              <p>Explore programmes that fit your goals.</p>
            </div>
          </div>
        </div>

        <p className="auth-copyright">
          FundBridge · Helping businesses connect with funding.
        </p>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-mobile-brand">
            <img src="/fundbridge-logo.png" alt="FundBridge" className="auth-logo-mobile" />
          </div>

          <p className="auth-eyebrow">
            ENTREPRENEUR WORKSPACE
          </p>

          <h2>
            {mode === "login" ? "Welcome back" : "Create your account"}
          </h2>

          <p className="auth-intro">
            {mode === "login"
              ? "Log in to continue to your FundBridge workspace."
              : "Create an account to start your funding journey."}
          </p>

          <div className="auth-tabs">
            <button
              type="button"
              className={mode === "login" ? "selected" : ""}
              onClick={() => changeMode("login")}
            >
              Log in
            </button>

            <button
              type="button"
              className={mode === "register" ? "selected" : ""}
              onClick={() => changeMode("register")}
            >
              Register
            </button>
          </div>

          {mode === "register" && (
            <div className="account-type-panel">
              <p className="auth-eyebrow">ACCOUNT TYPE</p>
              <div className="account-type-options">
                <button type="button" className={accountType === "ENTREPRENEUR" ? "selected" : ""} onClick={() => setAccountType("ENTREPRENEUR")}>Entrepreneur</button>
                <button type="button" className={accountType === "ORGANISATION" ? "selected" : ""} onClick={() => setAccountType("ORGANISATION")}>Organisation</button>
              </div>
              {accountType === "ORGANISATION" && (
                <div className="organisation-fields">
                  <label>Organisation name<input value={organisationName} onChange={(event) => setOrganisationName(event.target.value)} required /></label>
                  <label>Organisation type<input value={organisationType} onChange={(event) => setOrganisationType(event.target.value)} placeholder="Company, NGO, funder..." /></label>
                  <label>Location<input value={location} onChange={(event) => setLocation(event.target.value)} placeholder="City, province" /></label>
                </div>
              )}
            </div>
          )}
          {error && (
            <div className="auth-alert auth-error" role="alert">
              {error}
            </div>
          )}

          {success && (
            <div className="auth-alert auth-success" role="status">
              {success}
            </div>
          )}

          <form onSubmit={handleSubmit} className="auth-form">
            {mode === "register" && (
              <label>
                Full name
                <input
                  type="text"
                  value={name}
                  onChange={(event) => setName(event.target.value)}
                  placeholder="Enter your full name"
                  autoComplete="name"
                  maxLength={100}
                  required
                />
              </label>
            )}

            <label>
              Email address
              <input
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                autoComplete="email"
                required
              />
            </label>

            <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter your password"
                autoComplete={
                  mode === "login" ? "current-password" : "new-password"
                }
                minLength={8}
                required
              />
            </label>

            {mode === "register" && (
              <label>
                Confirm password
                <input
                  type="password"
                  value={confirmPassword}
                  onChange={(event) =>
                    setConfirmPassword(event.target.value)
                  }
                  placeholder="Enter your password again"
                  autoComplete="new-password"
                  minLength={8}
                  required
                />
              </label>
            )}

            <button
              className="auth-submit"
              type="submit"
              disabled={loading}
            >
              {loading
                ? "Please wait..."
                : mode === "login"
                  ? "Log in to FundBridge →"
                  : "Create entrepreneur account →"}
            </button>
          </form>

          <p className="auth-switch">
            {mode === "login"
              ? "New to FundBridge?"
              : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={() =>
                changeMode(mode === "login" ? "register" : "login")
              }
            >
              {mode === "login" ? "Create an account" : "Log in"}
            </button>
          </p>        </div>
      </section>
    </main>
  );
}



