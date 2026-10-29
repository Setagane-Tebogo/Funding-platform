import { useEffect, useState } from "react";
import "./BusinessProfile.css";
import LocationPicker from "./LocationPicker.jsx";
const API = window.location.hostname === "localhost" ? (import.meta.env.VITE_API_URL || "http://localhost:8080") : "https://funding-platform-4vyt.onrender.com";
const BUSINESS_TYPE_GROUPS = {
  "Retail": [["grocery", "Convenience or grocery store"], ["clothing", "Clothing or fashion shop"], ["electronics", "Electronics or mobile phone shop"], ["other", "Other retail business"]],
  "Food and hospitality": [["restaurant", "Restaurant or takeaway"], ["cafe", "Cafe or coffee shop"], ["bakery", "Bakery or confectionery"], ["catering", "Catering or food service"], ["other", "Other food business"]],
  "Personal services": [["salon", "Hair salon, barber, or beauty service"], ["laundry", "Laundry or dry cleaning"], ["tailoring", "Tailoring or clothing repairs"], ["other", "Other personal service"]],
  "Health and care": [["health", "Pharmacy, clinic, or medical practice"], ["veterinary", "Veterinary practice"], ["other", "Other health or care business"]],
  "Education": [["education", "Daycare, school, or tutoring"], ["training", "Training or learning centre"], ["other", "Other education business"]],
  "Tourism": [["accommodation", "Guesthouse, hotel, or accommodation"], ["travel", "Travel agency or tour service"], ["other", "Other tourism business"]],
  "Automotive": [["automotive", "Car repair, mechanic, parts, or tyre shop"], ["carwash", "Car wash"], ["other", "Other automotive business"]],
  "Professional services": [["professional", "IT, software, or technology service"], ["accounting", "Accounting or bookkeeping service"], ["legal", "Legal or consulting practice"], ["other", "Other professional service"]],
  "Agriculture": [["agriculture", "Farm or agricultural producer"], ["farm_supply", "Agricultural supplies business"], ["other", "Other agriculture business"]],
  "Manufacturing and trades": [["manufacturing", "Manufacturer or production workshop"], ["construction", "Construction or skilled trade workshop"], ["other", "Other manufacturing or trade business"]],
  "Transport and logistics": [["transport", "Taxi or passenger transport"], ["logistics", "Delivery or logistics service"], ["other", "Other transport business"]],
  "Other": [["other", "Other business type"]],
};
const INDUSTRIES = Object.keys(BUSINESS_TYPE_GROUPS);
const BUSINESS_STAGES = ["Micro / Start-up", "Small / Early-stage", "Medium / Growth", "Large / Established"];
function restoreFinancialInputs(inputs = {}, profileFundingNeeded = "") {
  const provided = inputs.providedFields;
  const hasHistory = Array.isArray(provided);
  const isProvided = (key) => !hasHistory || provided.includes(key);
  const legacy = !hasHistory || !Object.prototype.hasOwnProperty.call(inputs, "fundingRequired");
  return {
    fundingNeeded: legacy ? (inputs.fundingRequired ?? inputs.startupCosts ?? profileFundingNeeded ?? "") : (isProvided("fundingRequired") ? (inputs.fundingRequired ?? "") : ""),
    startupCosts: isProvided("startupCosts") ? (inputs.startupCosts ?? "") : "",
    monthlyRevenue: isProvided("monthlyRevenue") ? (inputs.monthlyRevenue ?? "") : "",
    monthlyExpenses: isProvided("monthlyExpenses") ? (inputs.monthlyExpenses ?? "") : "",
    monthlyGrowthPercent: isProvided("monthlyGrowthPercent") ? (inputs.monthlyGrowthPercent ?? "") : "",
    totalAssets: isProvided("totalAssets") ? (inputs.totalAssets ?? "") : "",
    totalLiabilities: isProvided("totalLiabilities") ? (inputs.totalLiabilities ?? "") : "",
    cashOnHand: (provided.includes("availableCapital") || isProvided("cashOnHand")) ? (inputs.availableCapital ?? inputs.cashOnHand ?? "") : "",
    customerCount: isProvided("customerCount") ? (inputs.customerCount ?? "") : "",
    employees: isProvided("employees") ? (inputs.employees ?? "") : "",
    targetMarket: inputs.targetMarket ?? "",
    businessExperience: inputs.businessExperience ?? "",
    operationsPlan: inputs.operationsPlan ?? "",
    riskMitigation: inputs.riskMitigation ?? "",
  };
}
function normalizeBusinessStage(value) {
  if (BUSINESS_STAGES.includes(value)) return value;
  const stage = (value || "").toLowerCase();
  if (stage.includes("startup") || stage.includes("start-up") || stage.includes("idea")) return BUSINESS_STAGES[0];
  if (stage.includes("early") || stage.includes("small")) return BUSINESS_STAGES[1];
  if (stage.includes("growth") || stage.includes("medium")) return BUSINESS_STAGES[2];
  if (stage.includes("established") || stage.includes("large") || stage.includes("scale")) return BUSINESS_STAGES[3];
  return "";
}
const empty = { businessName: "", industry: "", businessTypeCategory: "", customBusinessType: "", customIndustry: "", businessStage: "", description: "", location: "", latitude: "", longitude: "", fundingNeeded: "", startupCosts: "", intendedUseOfFunds: "", monthlyRevenue: "", monthlyExpenses: "", monthlyGrowthPercent: "", totalAssets: "", totalLiabilities: "", cashOnHand: "", customerCount: "", employees: "", targetMarket: "", businessExperience: "", operationsPlan: "", riskMitigation: "" };
function getBusinessTypeLabel(form) {
  if (form.businessTypeCategory === "other") return form.customBusinessType || "this business";
  return (BUSINESS_TYPE_GROUPS[form.industry] || []).find(([key]) => key === form.businessTypeCategory)?.[1] || "this business";
}
function getIndustryValue(form) { return form.industry === "Other" ? (form.customIndustry || "Other") : form.industry; }
function formatRand(value) {
  return value == null ? "Not provided" : `R${Number(value).toLocaleString("en-ZA", { maximumFractionDigits: 2 })}`;
}
function AssessmentDashboard({ data, history = [] }) {
  const result = data?.viabilityAssessment;
  if (!result) return <p>Run an assessment to see the business viability result.</p>;
  const financials = result.financials || {};
  const previous = history.find((item) => item.assessmentId !== result.assessmentId);
  const change = previous ? result.score - previous.score : null;
  const location = result.locationEvidence || {};
  return <div className="viability-dashboard">
    <section className="viability-score-hero">
      <div className="viability-gauge" role="img" aria-label={`Business viability score ${result.score} out of 100`} style={{ "--score-angle": `${Number(result.score) * 3.6}deg` }}><div><strong>{result.score}</strong><span>/100</span></div></div>
      <div className="viability-summary"><p className="profile-eyebrow">BUSINESS VIABILITY</p><h3>{result.band}</h3><p className="viability-prediction">{result.prediction}</p><p>{result.predictionDisclaimer}</p><div className="viability-confidence"><strong>{result.confidence} confidence</strong><span>{result.dataCompletenessPercent}% of key information supplied</span></div>{change != null && <small>Since the previous assessment: {change > 0 ? "+" : ""}{change} points (previous score {previous.score}).</small>}</div>
    </section>
    <section className="viability-financials"><h3>Monthly financial estimate</h3><div className="viability-metric-grid"><div><span>Revenue</span><strong>{formatRand(financials.monthlyRevenue)}</strong></div><div><span>Expenses</span><strong>{formatRand(financials.monthlyExpenses)}</strong></div><div><span>Profit / loss</span><strong>{formatRand(financials.monthlyProfit)}</strong></div><div><span>Profit margin</span><strong>{financials.profitMarginPercent == null ? "Not available" : `${financials.profitMarginPercent}%`}</strong></div></div>{financials.breakEvenMonths != null && <p>Startup-cost payback at the entered monthly profit: <strong>{financials.breakEvenMonths} months</strong>.</p>}</section>
    <section className="viability-categories"><h3>Score breakdown</h3>{result.categoryScores?.map((item) => <div className="viability-category" key={item.key}><div><strong>{item.name}</strong><span>{item.score}/100 · {item.weight}% weight · {item.contribution} points</span></div><div className="viability-progress"><span style={{ width: `${item.score}%` }} /></div><p>{item.explanation}</p></div>)}</section>
    <section className="viability-two-column"><div><h3>What supports the business</h3><ul>{result.strengths?.map((item, index) => <li key={index}>{item}</li>)}</ul></div><div><h3>Key risks</h3><ul>{result.risks?.length ? result.risks.map((item, index) => <li key={index}>{item}</li>) : <li>No major risks were identified from the supplied information; important details may still be missing.</li>}</ul></div></section>
    <section className="viability-recommendations"><h3>Recommended next steps</h3><ol>{result.recommendations?.map((item, index) => <li key={index}>{item}</li>)}</ol></section>
    <section className="viability-insights"><h3>{result.sectorGuidance?.label || data.industry} and location</h3><p>{result.sectorGuidance?.focus}</p><p>{location.summary}</p><small>{location.coverageNote}</small></section>
    {result.missingInformation?.length > 0 && <details className="viability-missing"><summary>Missing information that could improve this assessment ({result.missingInformation.length})</summary><ul>{result.missingInformation.map((item) => <li key={item}>{item}</li>)}</ul></details>}
    {history.length > 1 && <details className="viability-history"><summary>Previous assessments ({history.length - 1})</summary><ol>{history.filter((item) => item.assessmentId !== result.assessmentId).map((item) => <li key={item.assessmentId}>{new Date(item.createdAt).toLocaleDateString()} · <strong>{item.score}/100</strong> · {item.band}</li>)}</ol></details>}
    <details className="viability-sources"><summary>Data sources and limitations</summary><p>{result.confidenceNote}</p><ul>{result.dataSources?.map((source) => <li key={source.name}><strong>{source.name}</strong> · {source.status}{source.license ? ` · ${source.license}` : ""}. {source.limitation} <a href={source.url} target="_blank" rel="noreferrer">Source information</a></li>)}</ul><p>Scores are weighted rule-based screening results, not statistically validated success probabilities. The proposal model is not trained because there are not yet enough real labelled FundBridge business outcomes.</p></details>
  </div>;
}

export default function BusinessProfile() {
  const [businesses, setBusinesses] = useState([]); const [selectedId, setSelectedId] = useState(null); const [form, setForm] = useState(empty); const [analysis, setAnalysis] = useState(null); const [assessmentHistory, setAssessmentHistory] = useState([]); const [loading, setLoading] = useState(true); const [loadError, setLoadError] = useState(""); const [saving, setSaving] = useState(false); const [analyzing, setAnalyzing] = useState(false); const [message, setMessage] = useState(""); const [error, setError] = useState(""); const [businessToDelete, setBusinessToDelete] = useState(null); const [deleting, setDeleting] = useState(false);
  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${sessionStorage.getItem("token")}` };
  async function loadAssessmentHistory(profileId, businessKey) {
    const params = new URLSearchParams();
    if (profileId) params.set("profileId", profileId);
    else if (businessKey) params.set("businessKey", businessKey);
    if (!profileId && !businessKey) { setAssessmentHistory([]); return; }
    try {
      const response = await fetch(`${API}/api/entrepreneur/business-assessments?${params}`, { headers });
      const data = await response.json().catch(() => []);
      if (response.ok && Array.isArray(data)) setAssessmentHistory(data);
    } catch { setAssessmentHistory([]); }
  }
  async function load() {
    const controller = new AbortController();
    const timeout = window.setTimeout(() => controller.abort(), 30000);
    setLoading(true);
    setLoadError("");
    try {
      const response = await fetch(`${API}/api/entrepreneur/business-profiles`, { headers, signal: controller.signal });
      const data = await response.json().catch(() => null);
      if (!response.ok) {
        if (response.status === 401) throw new Error("Your session has expired. Log out and sign in again.");
        throw new Error(data?.detail || `Could not load your businesses (HTTP ${response.status}).`);
      }
      if (!Array.isArray(data)) throw new Error("The server returned an invalid business list.");
      setBusinesses(data);
      if (data[0] && !selectedId) selectBusiness(data[0]);
    } catch (loadError) {
      setLoadError(controller.signal.aborted
        ? "The request timed out. Check your connection and try again."
        : loadError.message || "Could not connect to the server. Check your connection and try again.");
    } finally {
      window.clearTimeout(timeout);
      setLoading(false);
    }
  }
  useEffect(() => { const timer = window.setTimeout(load, 0); return () => window.clearTimeout(timer); }, []);
  useEffect(() => {
    if (!businessToDelete) return undefined;
    function handleEscape(event) {
      if (event.key === "Escape" && !deleting) setBusinessToDelete(null);
    }
    window.addEventListener("keydown", handleEscape);
    return () => window.removeEventListener("keydown", handleEscape);
  }, [businessToDelete, deleting]);
  function selectBusiness(item) {
    const industryKnown = INDUSTRIES.includes(item.industry);
    const industry = industryKnown ? item.industry : "Other";
    const businessTypes = BUSINESS_TYPE_GROUPS[industry] || [];
    const savedType = item.analysis?.businessTypeCategory ?? "";
    const businessTypeCategory = businessTypes.some(([key]) => key === savedType) ? savedType : "";
    setSelectedId(item.id);
    setForm({ ...empty, ...item, businessStage: normalizeBusinessStage(item.businessStage), industry, customIndustry: industryKnown ? "" : (item.industry || ""), latitude: item.analysis?.locationAnalysis?.coordinates?.latitude ?? "", longitude: item.analysis?.locationAnalysis?.coordinates?.longitude ?? "", businessTypeCategory, customBusinessType: item.analysis?.customBusinessType ?? "", ...restoreFinancialInputs(item.analysis?.financialInputs, item.fundingNeeded ?? "") });
    setAnalysis(item.analysis?.businessTypeCategory && businessTypeCategory ? item.analysis : null);
    loadAssessmentHistory(item.id, item.analysis?.businessKey);
    setMessage(""); setError("");
  }
  function changeIndustry(value) {
    setForm((current) => ({ ...current, industry: value, customIndustry: "", businessTypeCategory: "", customBusinessType: "" }));
    setAnalysis(null); setMessage(""); setError("");
  }
  function newBusiness() { setSelectedId(null); setForm(empty); setAnalysis(null); setAssessmentHistory([]); setMessage(""); setError(""); }
  function updateField(field, value) { setForm((current) => ({ ...current, [field]: value })); setAnalysis(null); setMessage(""); setError(""); }
  function updateLocation(value) { setForm((current) => ({ ...current, location: value.location, latitude: value.latitude, longitude: value.longitude })); setAnalysis(null); setMessage(""); setError(""); }
  async function save(event) { event.preventDefault(); if (form.industry === "Other" && !form.customIndustry.trim()) { setError("Describe the industry sector before publishing."); return; } if (!form.location || form.latitude === "" || form.longitude === "") { setError("Choose the business location by searching or placing a pin on the map before publishing."); return; } setSaving(true); setMessage(""); setError(""); const payload = { businessName: form.businessName, industry: getIndustryValue(form), businessStage: form.businessStage, description: form.description, location: form.location, fundingNeeded: form.fundingNeeded ? Number(form.fundingNeeded) : null, intendedUseOfFunds: form.intendedUseOfFunds || null }; const url = selectedId ? `${API}/api/entrepreneur/business-profiles/${selectedId}` : `${API}/api/entrepreneur/business-profile`; const response = await fetch(url, { method: selectedId ? "PUT" : "POST", headers, body: JSON.stringify({ ...payload, analysis }) }); const data = await response.json().catch(() => null); if (!response.ok) setError(data?.detail || "Could not save business."); else { setMessage("Business proposal saved and published."); setSelectedId(data.id); setAnalysis(data.analysis || null); await load(); } setSaving(false); }
  async function remove() {
    if (!businessToDelete) return;
    setDeleting(true);
    setError("");
    try {
      const response = await fetch(`${API}/api/entrepreneur/business-profiles/${businessToDelete.id}`, { method: "DELETE", headers });
      if (!response.ok) {
        const data = await response.json().catch(() => null);
        throw new Error(data?.detail || `Could not delete business (HTTP ${response.status}).`);
      }
      setBusinessToDelete(null);
      newBusiness();
      await load();
      setMessage("Business proposal deleted.");
    } catch (deleteError) {
      setError(deleteError.message || "Could not delete business. Please try again.");
    } finally {
      setDeleting(false);
    }
  }
  async function analyse() {
    if (!form.industry) { setError("Choose an industry sector before running the assessment."); return; }
    if (form.industry === "Other" && !form.customIndustry.trim()) { setError("Describe the industry sector before running the assessment."); return; }
    if (!form.businessTypeCategory) { setError("Choose the kind of business before running the assessment."); return; }
    if (form.businessTypeCategory === "other" && !form.customBusinessType.trim()) { setError("Describe the kind of business before running the assessment."); return; }
    if (form.latitude === "" || form.longitude === "" || !form.location) { setError("Select the business location on the map before running the assessment."); return; }
    const fields = {
      startupCosts: "startupCosts", availableCapital: "cashOnHand", fundingRequired: "fundingNeeded",
      monthlyRevenue: "monthlyRevenue", monthlyExpenses: "monthlyExpenses",
      targetMarket: "targetMarket", businessExperience: "businessExperience",
      operationsPlan: "operationsPlan", riskMitigation: "riskMitigation",
    };
    const providedInputs = Object.entries(fields).filter(([, field]) => String(form[field] ?? "").trim() !== "").map(([key]) => key);
    if (form.customerCount !== "") providedInputs.push("customerCount");
    setAnalyzing(true); setError(""); setMessage(""); setAnalysis(null);
    try {
      const payload = {
        ...(selectedId ? { profileId: selectedId } : {}),
        businessName: form.businessName, industry: getIndustryValue(form),
        businessType: form.businessTypeCategory === "other" ? form.customBusinessType.trim() : getBusinessTypeLabel(form),
        businessTypeCategory: form.businessTypeCategory, customBusinessType: form.customBusinessType.trim(),
        businessStage: form.businessStage, location: form.location, latitude: Number(form.latitude), longitude: Number(form.longitude),
        businessDescription: form.description, startupCosts: form.startupCosts === "" ? null : Number(form.startupCosts),
        availableCapital: form.cashOnHand === "" ? null : Number(form.cashOnHand),
        fundingRequired: form.fundingNeeded === "" ? null : Number(form.fundingNeeded),
        monthlyRevenue: form.monthlyRevenue === "" ? null : Number(form.monthlyRevenue),
        monthlyExpenses: form.monthlyExpenses === "" ? null : Number(form.monthlyExpenses),
        monthlyGrowthPercent: form.monthlyGrowthPercent === "" ? null : Number(form.monthlyGrowthPercent),
        totalAssets: form.totalAssets === "" ? null : Number(form.totalAssets),
        totalLiabilities: form.totalLiabilities === "" ? null : Number(form.totalLiabilities),
        customerCount: Number(form.customerCount || 0), employees: Number(form.employees || 0),
        targetMarket: form.targetMarket, businessExperience: form.businessExperience,
        operationsPlan: form.operationsPlan, riskMitigation: form.riskMitigation, providedInputs,
      };
      const response = await fetch(API + "/api/entrepreneur/business-assessments", { method: "POST", headers, body: JSON.stringify(payload) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "Could not assess this business.");
      const result = data;
      setAnalysis(result);
      setAssessmentHistory(data.assessmentHistory || []);
      await loadAssessmentHistory(selectedId, data.businessKey);
      setMessage("Assessment completed and saved to your history.");
    } catch (assessmentError) {
      setError(assessmentError.message || "Could not assess this business.");
    } finally {
      setAnalyzing(false);
    }
  }
  if (loading) return <div className="profile-panel" role="status" aria-live="polite">Loading businesses...</div>;
  if (loadError) return <div className="profile-panel" role="alert"><h2>Couldn’t load your businesses</h2><p>{loadError}</p><button type="button" className="secondary-button" onClick={load}>Try again</button></div>;
  return <section className="business-profile-page"><div className="profile-heading"><p className="profile-eyebrow">MY BUSINESSES</p><h1>Business proposals</h1><p>Complete the business details, analyse the numbers, then publish the proposal for funders to review.</p></div><div className="business-switcher">{businesses.map((item) => <button type="button" className={selectedId === item.id ? "selected" : ""} key={item.id} onClick={() => selectBusiness(item)}>{item.businessName}</button>)}<button type="button" className="new-business" onClick={newBusiness}>Add another business</button></div>{message && <div className="profile-message success">{message}</div>}{error && !businessToDelete && <div className="profile-message error">{error}</div>}<form className="profile-panel" onSubmit={save}><h2>{selectedId ? "Edit business proposal" : "New business proposal"}</h2><div className="profile-form-grid"><label>Business name *<input value={form.businessName} onChange={(e) => updateField("businessName", e.target.value)} required /></label><label>Industry sector *<select value={form.industry} onChange={(e) => changeIndustry(e.target.value)} required><option value="">Choose an industry sector</option>{INDUSTRIES.map((industry) => <option key={industry} value={industry}>{industry}</option>)}</select></label>{form.industry === "Other" && <label>Describe the industry sector *<input value={form.customIndustry} onChange={(e) => updateField("customIndustry", e.target.value)} placeholder="For example, renewable energy" required /></label>}<label>Business size / stage *<select value={form.businessStage} onChange={(e) => updateField("businessStage", e.target.value)} required><option value="">Choose the business size / stage</option>{BUSINESS_STAGES.map((stage) => <option key={stage} value={stage}>{stage}</option>)}</select></label><label>What kind of business is it? *<select value={form.businessTypeCategory} onChange={(e) => updateField("businessTypeCategory", e.target.value)} required disabled={!form.industry}><option value="">{form.industry ? "Choose a business type" : "Choose an industry first"}</option>{(BUSINESS_TYPE_GROUPS[form.industry] || []).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>{form.businessTypeCategory === "other" && <label>Describe the business type *<input value={form.customBusinessType} onChange={(e) => updateField("customBusinessType", e.target.value)} placeholder="Describe the specific business" required /></label>}<div className="full-width"><LocationPicker value={form} onChange={updateLocation} /></div><label className="full-width">Business description *<textarea value={form.description} onChange={(e) => updateField("description", e.target.value)} rows="5" required /></label><label>Startup costs / capital needed to open (ZAR)<input type="number" min="0" value={form.startupCosts} onChange={(e) => updateField("startupCosts", e.target.value)} /></label><label>Funding required (ZAR)<input type="number" min="0" value={form.fundingNeeded} onChange={(e) => updateField("fundingNeeded", e.target.value)} /></label><label>Intended use of funds<input value={form.intendedUseOfFunds} onChange={(e) => updateField("intendedUseOfFunds", e.target.value)} /></label><label>Expected monthly revenue<input type="number" min="0" value={form.monthlyRevenue} onChange={(e) => updateField("monthlyRevenue", e.target.value)} /></label><label>Expected monthly expenses<input type="number" min="0" value={form.monthlyExpenses} onChange={(e) => updateField("monthlyExpenses", e.target.value)} /></label><label>Expected monthly growth (%)<input type="number" min="0" value={form.monthlyGrowthPercent} onChange={(e) => updateField("monthlyGrowthPercent", e.target.value)} /></label><label>Total assets (ZAR)<input type="number" min="0" value={form.totalAssets} onChange={(e) => updateField("totalAssets", e.target.value)} /></label><label>Total liabilities (ZAR)<input type="number" min="0" value={form.totalLiabilities} onChange={(e) => updateField("totalLiabilities", e.target.value)} /></label><label>Available capital (cash on hand, ZAR)<input type="number" min="0" value={form.cashOnHand} onChange={(e) => updateField("cashOnHand", e.target.value)} /></label><label>Current customers<input type="number" min="0" value={form.customerCount} onChange={(e) => updateField("customerCount", e.target.value)} /></label><label>Employees<input type="number" min="0" value={form.employees} onChange={(e) => updateField("employees", e.target.value)} /></label><details className="assessment-extra-fields full-width"><summary>Optional assessment details</summary><label>Target market and evidence of demand<textarea value={form.targetMarket} onChange={(e) => updateField("targetMarket", e.target.value)} rows="3" placeholder="Who will buy, and what evidence do you have?" /></label><label>Relevant business experience<textarea value={form.businessExperience} onChange={(e) => updateField("businessExperience", e.target.value)} rows="2" placeholder="Optional; your profile bio may already provide context." /></label><label>Operations, suppliers, and infrastructure plan<textarea value={form.operationsPlan} onChange={(e) => updateField("operationsPlan", e.target.value)} rows="3" placeholder="Suppliers, transport, electricity, water, internet, permits, or delivery arrangements relevant to this business." /></label><label>Risk and contingency plan<textarea value={form.riskMitigation} onChange={(e) => updateField("riskMitigation", e.target.value)} rows="2" placeholder="For example, seasonal planning, backup suppliers, insurance, or reserve funds." /></label></details></div><div className="profile-form-footer"><button type="button" className="secondary-button" onClick={analyse} disabled={analyzing || saving}>{analyzing ? "Analysing..." : "Analyse business"}</button><button type="submit" disabled={saving || analyzing || !analysis}>{saving ? "Publishing..." : "Publish proposal"}</button>{selectedId && <button type="button" className="danger-button" onClick={() => setBusinessToDelete({ id: selectedId, businessName: form.businessName })}>Delete proposal</button>}</div></form>{(selectedId || analysis || analyzing) && <section className="analysis-box"><p className="profile-eyebrow">BUSINESS ASSESSMENT</p><h2>Business viability</h2><p>The score combines your submitted business details with available mapped surroundings. It is an indicative screening assessment, not a guarantee of success.</p><button type="button" onClick={analyse} disabled={analyzing || saving}>{analyzing ? "Assessing..." : "Run viability assessment"}</button>{analyzing && <p role="status">Checking the business details and nearby mapped context...</p>}{analysis && <div className="analysis-result"><AssessmentDashboard data={analysis} history={assessmentHistory} /></div>}</section>}{businessToDelete && <div className="modal-backdrop business-delete-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !deleting) setBusinessToDelete(null); }}><section className="confirm-modal business-delete-modal" role="dialog" aria-modal="true" aria-labelledby="delete-business-title" aria-describedby="delete-business-description"><h2 id="delete-business-title">Delete this proposal?</h2><p id="delete-business-description">Delete <strong>{businessToDelete.businessName || "this business proposal"}</strong>? This can’t be undone.</p>{error && <div className="profile-message error" role="alert">{error}</div>}<div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setBusinessToDelete(null)} disabled={deleting}>Cancel</button><button type="button" className="danger-button" onClick={remove} disabled={deleting}>{deleting ? "Deleting..." : "Delete"}</button></div></section></div>}</section>;
}
