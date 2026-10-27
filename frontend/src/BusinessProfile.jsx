
import { useEffect, useState } from "react";
import "./BusinessProfile.css";

const API_ROOT = import.meta.env.VITE_API_URL || (window.location.hostname === "localhost" ? "http://localhost:8080" : "https://funding-platform-4vyt.onrender.com");
const API_URL = `${API_ROOT}/api/entrepreneur/business-profile`;

const emptyForm = {
  businessName: "",
  industry: "",
  businessStage: "",
  description: "",
  location: "",
  fundingNeeded: "",
  intendedUseOfFunds: "",
};

function BusinessProfile() {
  const [form, setForm] = useState(emptyForm);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [exists, setExists] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [analysis, setAnalysis] = useState(null);
  const [analysing, setAnalysing] = useState(false);

  async function loadProfile() {
    const token = sessionStorage.getItem("token");

    if (!token) {
      setError("Please log in first. No authentication token was found.");
      setLoading(false);
      return;
    }

    try {
      const response = await fetch(API_URL, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
      });

      if (response.status === 404) {
        setExists(false);
        return;
      }

      if (!response.ok) {
        throw new Error(
          response.status === 401
            ? "Your session has expired. Please log in again."
            : `Could not load profile (HTTP ${response.status}).`
        );
      }

      const data = await response.json();

      setForm({
        businessName: data.businessName ?? "",
        industry: data.industry ?? "",
        businessStage: data.businessStage ?? "",
        description: data.description ?? "",
        location: data.location ?? "",
        fundingNeeded: data.fundingNeeded ?? "",
        intendedUseOfFunds: data.intendedUseOfFunds ?? "",
      });

      setExists(true);
    } catch (err) {
      setError(err.message || "Could not connect to the backend.");
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    const timer = window.setTimeout(() => loadProfile(), 0);
    return () => window.clearTimeout(timer);
  }, []);

  function handleChange(event) {
    const { name, value } = event.target;

    setForm((previous) => ({
      ...previous,
      [name]: value,
    }));
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setSaving(true);
    setMessage("");
    setError("");

    const token = sessionStorage.getItem("token");

    if (!token) {
      setError("Please log in before saving your profile.");
      setSaving(false);
      return;
    }

    const payload = {
      ...form,
      fundingNeeded: form.fundingNeeded
        ? Number(form.fundingNeeded)
        : null,
    };

    try {
      const response = await fetch(API_URL, {
        method: exists ? "PUT" : "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${token}`,
        },
        body: JSON.stringify(payload),
      });

      const result = await response.json().catch(() => null);

      if (!response.ok) {
        throw new Error(
          typeof result === "string"
            ? result
            : result?.message ||
              `Could not save profile (HTTP ${response.status}).`
        );
      }

      setForm({
        ...emptyForm,
        ...result,
        fundingNeeded: result.fundingNeeded ?? "",
      });

      setExists(true);
      setMessage("Your business profile has been saved successfully.");
    } catch (err) {
      setError(err.message || "Could not save your profile.");
    } finally {
      setSaving(false);
    }
  }

  async function runAnalysis() {
    setAnalysing(true);
    setError("");
    try {
      const response = await fetch(`${API_ROOT}/api/entrepreneur/business-analysis`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${sessionStorage.getItem("token")}` },
        body: JSON.stringify({
          startupCosts: Number(form.fundingNeeded || 0),
          monthlyRevenue: Number(form.monthlyRevenue || 0),
          monthlyExpenses: Number(form.monthlyExpenses || 0),
          monthlyGrowthPercent: Number(form.monthlyGrowthPercent || 0),
        }),
      });
      const result = await response.json().catch(() => null);
      if (!response.ok) throw new Error(typeof result === "string" ? result : "Could not analyse the proposal.");
      setAnalysis(result);
    } catch (err) {
      setError(err.message || "Could not analyse the proposal.");
    } finally {
      setAnalysing(false);
    }
  }

  if (loading) {
    return <div className="profile-panel">Loading business profile...</div>;
  }

  return (
    <section className="business-profile-page">
      <div className="profile-heading">
        <p className="profile-eyebrow">ENTREPRENEUR WORKSPACE</p>
        <h1>Business Profile</h1>
        <p>
          Tell potential funders about your business, your goals, and the
          funding you need.
        </p>
      </div>

      {message && <div className="profile-message success">{message}</div>}
      {error && <div className="profile-message error">{error}</div>}

      <form className="profile-panel" onSubmit={handleSubmit}>
        <h2>Business information</h2>
        <p className="section-description">
          Complete the required fields to help funders understand your business.
        </p>

        <div className="profile-form-grid">
          <label>
            Business name *
            <input
              name="businessName"
              value={form.businessName}
              onChange={handleChange}
              required
              maxLength={255}
              placeholder="e.g. Tebogo Tech Solutions"
            />
          </label>

          <label>
            Industry *
            <select
              name="industry"
              value={form.industry}
              onChange={handleChange}
              required
            >
              <option value="">Select industry</option>
              <option value="Technology">Technology</option>
              <option value="Agriculture">Agriculture</option>
              <option value="Manufacturing">Manufacturing</option>
              <option value="Retail">Retail</option>
              <option value="Education">Education</option>
              <option value="Healthcare">Healthcare</option>
              <option value="Tourism">Tourism</option>
              <option value="Other">Other</option>
            </select>
          </label>

          <label>
            Business stage *
            <select
              name="businessStage"
              value={form.businessStage}
              onChange={handleChange}
              required
            >
              <option value="">Select stage</option>
              <option value="Idea">Idea</option>
              <option value="Startup">Startup</option>
              <option value="Early Revenue">Early revenue</option>
              <option value="Established">Established</option>
              <option value="Expansion">Expansion</option>
            </select>
          </label>

          <label>
            Business location *
            <input
              name="location"
              value={form.location}
              onChange={handleChange}
              required
              maxLength={255}
              placeholder="e.g. Polokwane, Limpopo"
            />
          </label>

          <label className="full-width">
            Business description *
            <textarea
              name="description"
              value={form.description}
              onChange={handleChange}
              required
              maxLength={2000}
              rows={5}
              placeholder="What does your business do, and what problem does it solve?"
            />
          </label>

          <label>
            Funding needed (ZAR)
            <input
              type="number"
              name="fundingNeeded"
              value={form.fundingNeeded}
              onChange={handleChange}
              min="0"
              step="0.01"
              placeholder="e.g. 150000"
            />
          </label>

          <label>
            Intended use of funds
            <input
              name="intendedUseOfFunds"
              value={form.intendedUseOfFunds}
              onChange={handleChange}
              maxLength={1000}
              placeholder="e.g. Equipment and development"
            />
          </label>

          <label>
            Expected monthly revenue (ZAR)
            <input type="number" name="monthlyRevenue" value={form.monthlyRevenue || ""} onChange={handleChange} min="0" step="0.01" placeholder="e.g. 50000" />
          </label>

          <label>
            Expected monthly expenses (ZAR)
            <input type="number" name="monthlyExpenses" value={form.monthlyExpenses || ""} onChange={handleChange} min="0" step="0.01" placeholder="e.g. 30000" />
          </label>

          <label>
            Expected monthly growth (%)
            <input type="number" name="monthlyGrowthPercent" value={form.monthlyGrowthPercent || ""} onChange={handleChange} min="0" step="0.1" placeholder="e.g. 5" />
          </label>
        </div>

        <div className="profile-form-footer">
          <span>* Required fields</span>
          <button type="submit" disabled={saving}>
            {saving
              ? "Saving..."
              : exists
                ? "Update business profile"
                : "Save business profile"}
          </button>
        </div>

        <div className="analysis-box">
          <div>
            <p className="profile-eyebrow">BUSINESS VIABILITY ANALYSIS</p>
            <h2>Estimate your path to profitability</h2>
            <p className="section-description">Use your proposal figures to receive an explainable break-even estimate.</p>
          </div>
          <button type="button" onClick={runAnalysis} disabled={analysing}>
            {analysing ? "Analysing..." : "Analyse proposal"}
          </button>
          {analysis && (
            <div className="analysis-result">
              <strong>{analysis.outlook}</strong>
              <p>{analysis.summary}</p>
              {analysis.estimatedBreakEvenMonths !== null && <p>Estimated break-even: <strong>{analysis.estimatedBreakEvenMonths} months</strong></p>}
              <p>Estimated monthly profit: R{Number(analysis.estimatedMonthlyProfit).toLocaleString()}</p>
              <small>{analysis.disclaimer}</small>
              {analysis.aiAssessment && (
                <div className="ai-assessment">
                  <strong>Grok assessment: {analysis.aiAssessment.recommendation}</strong>
                  <p>{analysis.aiAssessment.narrative}</p>
                  {analysis.aiAssessment.keyRisks?.length > 0 && <small>Key risks: {analysis.aiAssessment.keyRisks.join("; ")}</small>}
                </div>
              )}
            </div>
          )}
        </div>
      </form>
    </section>
  );
}

export default BusinessProfile;

