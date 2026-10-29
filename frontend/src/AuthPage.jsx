
import { useState } from "react";
import "./AuthPage.css";

const API_URL = `${window.location.hostname === "localhost" ? (import.meta.env.VITE_API_URL || "http://localhost:8080") : "https://funding-platform-4vyt.onrender.com"}/api/auth`;

export default function AuthPage({ onLogin }) {
  const [mode, setMode] = useState("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [otp, setOtp] = useState("");
  const [otpSent, setOtpSent] = useState(false);
  const [verificationSent, setVerificationSent] = useState(false);
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

    setOtpSent(false);
    setVerificationSent(false);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setError("");
    setSuccess("");

    if (mode === "register" && verificationSent) {
      setLoading(true);
      try {
        const response = await fetch(`${API_URL}/verify-email`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ email: email.trim(), code: otp }) });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.detail || "Could not verify your email.");
        setVerificationSent(false);
        setOtp("");
        setMode("login");
        setSuccess(data.message || "Email verified. You can now log in.");
      } catch (err) { setError(err.message); } finally { setLoading(false); }
      return;
    }
    if (mode === "forgot") {
      setLoading(true);
      try {
        const endpoint = otpSent ? "reset-password" : "forgot-password";
        const body = otpSent ? { email: email.trim(), otp, newPassword: password } : { email: email.trim() };
        const response = await fetch(`${API_URL}/${endpoint}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });
        const data = await response.json().catch(() => null);
        if (!response.ok) throw new Error(data?.detail || "Could not process password reset.");
        if (!otpSent) {
          setOtpSent(true);
          setSuccess(data.message);
        } else {
          changeMode("login");
          setSuccess(data.message || "Password reset successfully. You can now log in.");
        }
      } catch (err) { setError(err.message); } finally { setLoading(false); }
      return;
    }

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
        setVerificationSent(true);
        setOtp("");
        setSuccess(data?.message || "Check your email for the verification code.");
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
          <img src="/fundbridge-logo-transparent.png" alt="FundBridge" className="auth-logo" />
          
        </div>

        <div className="auth-brand-content">
          <p className="auth-eyebrow">A BETTER WAY TO FIND YOUR NEXT STEP</p>
          <h1>Make room for what your business could become.</h1>
          <p>
            Put your business in front of funders, find programmes that fit,
            and keep the conversation moving.
          </p>

          <div className="auth-feature">
            <span aria-hidden="true"></span>
            <div>
              <strong>One business profile</strong>
              <p>Present your business and funding needs.</p>
            </div>
          </div>

          <div className="auth-feature">
            <span aria-hidden="true"></span>
            <div>
              <strong>Funding opportunities</strong>
              <p>Explore programmes that fit your goals.</p>
            </div>
          </div>
        </div>

        <p className="auth-copyright">
          FundBridge - Helping businesses connect with funding.
        </p>
      </section>

      <section className="auth-form-panel">
        <div className="auth-form-container">
          <div className="auth-mobile-brand">
            <img src="/fundbridge-logo-transparent.png" alt="FundBridge" className="auth-logo-mobile" />
          </div>

          <p className="auth-eyebrow">
            FUNDING, WITH A CLEARER WAY FORWARD
          </p>

          <h2>
            {mode === "login" ? "Welcome back" : mode === "forgot" ? "Reset your password" : "Create your account"}
          </h2>

          <p className="auth-intro">
            {mode === "login"
              ? "Log in to continue to FundBridge."
              : mode === "forgot" ? "Recover access to your FundBridge account."
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
            {mode === "forgot" && otpSent && <label>OTP code<input value={otp} onChange={(event) => setOtp(event.target.value)} inputMode="numeric" maxLength={6} required /></label>}
            {mode === "register" && verificationSent && <label>Verification code<input value={otp} onChange={(event) => setOtp(event.target.value)} inputMode="numeric" maxLength={6} required /></label>}

            {(mode !== "forgot" || otpSent) && <label>
              Password
              <input
                type="password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder={mode === "forgot" ? "Choose a new password" : "Enter your password"}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                minLength={8}
                required
              />
            </label>}

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
                  ? "Log in to FundBridge"
                  : mode === "forgot" ? (otpSent ? "Reset password" : "Send reset code")
                  : mode === "register" && verificationSent ? "Verify email"
                  : "Create entrepreneur account"}
            </button>
          </form>

          {mode === "login" && <button type="button" className="forgot-link" onClick={() => changeMode("forgot")}>Forgot password?</button>}
          {mode === "forgot" && <p className="auth-reset-hint">{otpSent ? "Enter the six-digit code from your email and choose a new password." : "We will email you a six-digit reset code."}</p>}
          <p className="auth-switch">
            {mode === "login"
              ? "New to FundBridge?"
              : mode === "forgot" ? "Remembered your password?" : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={() =>
                changeMode(mode === "login" ? "register" : "login")
              }
            >
              {mode === "login" ? "Create an account" : "Log in"}
            </button>
          </p>
        </div>
      </section>
    </main>
  );
}
















