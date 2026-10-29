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
  "Other": [["other", "Other business type"]],
};
const INDUSTRIES = Object.keys(BUSINESS_TYPE_GROUPS);
const BUSINESS_STAGES = ["Micro / Start-up", "Small / Early-stage", "Medium / Growth", "Large / Established"];
function normalizeBusinessStage(value) {
  if (BUSINESS_STAGES.includes(value)) return value;
  const stage = (value || "").toLowerCase();
  if (stage.includes("startup") || stage.includes("start-up") || stage.includes("idea")) return BUSINESS_STAGES[0];
  if (stage.includes("early") || stage.includes("small")) return BUSINESS_STAGES[1];
  if (stage.includes("growth") || stage.includes("medium")) return BUSINESS_STAGES[2];
  if (stage.includes("established") || stage.includes("large") || stage.includes("scale")) return BUSINESS_STAGES[3];
  return "";
}
const empty = { businessName: "", industry: "", businessTypeCategory: "", customBusinessType: "", customIndustry: "", businessStage: "", description: "", location: "", latitude: "", longitude: "", fundingNeeded: "", intendedUseOfFunds: "", monthlyRevenue: "", monthlyExpenses: "", monthlyGrowthPercent: "", totalAssets: "", totalLiabilities: "", cashOnHand: "", customerCount: "", employees: "" };
function getBusinessTypeLabel(form) {
  if (form.businessTypeCategory === "other") return form.customBusinessType || "this business";
  return (BUSINESS_TYPE_GROUPS[form.industry] || []).find(([key]) => key === form.businessTypeCategory)?.[1] || "this business";
}
function getIndustryValue(form) { return form.industry === "Other" ? (form.customIndustry || "Other") : form.industry; }
function formatAdvancedRatios(value) {
  if (Array.isArray(value)) return value.join(", ");
  return typeof value === "string" ? value : "";
}

export default function BusinessProfile() {
  const [businesses, setBusinesses] = useState([]); const [selectedId, setSelectedId] = useState(null); const [form, setForm] = useState(empty); const [analysis, setAnalysis] = useState(null); const [advancedRatios, setAdvancedRatios] = useState(""); const [loading, setLoading] = useState(true); const [loadError, setLoadError] = useState(""); const [saving, setSaving] = useState(false); const [analyzing, setAnalyzing] = useState(false); const [message, setMessage] = useState(""); const [error, setError] = useState(""); const [businessToDelete, setBusinessToDelete] = useState(null); const [deleting, setDeleting] = useState(false);
  const headers = { "Content-Type": "application/json", Authorization: `Bearer ${sessionStorage.getItem("token")}` };
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
    setForm({ ...empty, ...item, businessStage: normalizeBusinessStage(item.businessStage), industry, customIndustry: industryKnown ? "" : (item.industry || ""), latitude: item.analysis?.locationAnalysis?.coordinates?.latitude ?? "", longitude: item.analysis?.locationAnalysis?.coordinates?.longitude ?? "", businessTypeCategory, customBusinessType: item.analysis?.customBusinessType ?? "", ...(item.analysis?.financialInputs || {}), fundingNeeded: item.fundingNeeded || item.analysis?.financialInputs?.startupCosts || "" });
    setAnalysis(item.analysis?.businessTypeCategory && businessTypeCategory ? item.analysis : null);
    setAdvancedRatios(formatAdvancedRatios(item.analysis?.financialRatios)); setMessage(""); setError("");
  }
  function changeIndustry(value) {
    setForm((current) => ({ ...current, industry: value, customIndustry: "", businessTypeCategory: "", customBusinessType: "" }));
    setAnalysis(null); setMessage(""); setError("");
  }
  function newBusiness() { setSelectedId(null); setForm(empty); setAnalysis(null); setAdvancedRatios(""); setMessage(""); setError(""); }
  function updateField(field, value) { setForm((current) => ({ ...current, [field]: value })); setAnalysis(null); setMessage(""); setError(""); }
  function updateLocation(value) { setForm((current) => ({ ...current, location: value.location, latitude: value.latitude, longitude: value.longitude })); setAnalysis(null); setMessage(""); setError(""); }
  function updateAdvancedRatios(value) { setAdvancedRatios(value); setAnalysis(null); setMessage(""); setError(""); }
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
    if (!form.industry) { setError("Choose an industry sector before running the analysis."); return; }
    if (form.industry === "Other" && !form.customIndustry.trim()) { setError("Describe the industry sector before running the analysis."); return; }
    if (!form.businessTypeCategory) { setError("Choose the kind of business before running the analysis."); return; }
    if (form.businessTypeCategory === "other" && !form.customBusinessType.trim()) { setError("Describe the kind of business before running the analysis."); return; }
    if (form.latitude === "" || form.longitude === "" || !form.location) { setError("Select the business location on the map before running the analysis."); return; }
    const ratios = advancedRatios.split(",").map((value) => Number(value.trim())).filter((value) => Number.isFinite(value));
    if (advancedRatios.trim() && ratios.length !== 64) {
      setError("The public model requires exactly 64 accounting ratios, separated by commas.");
      return;
    }
    setAnalyzing(true);
    setError("");
    setMessage("");
    setAnalysis(null);
    try {
      const payload = { ...(selectedId ? { profileId: selectedId } : {}), startupCosts: Number(form.fundingNeeded || 0), monthlyRevenue: Number(form.monthlyRevenue || 0), monthlyExpenses: Number(form.monthlyExpenses || 0), monthlyGrowthPercent: Number(form.monthlyGrowthPercent || 0), totalAssets: Number(form.totalAssets || 0), totalLiabilities: Number(form.totalLiabilities || 0), cashOnHand: Number(form.cashOnHand || 0), customerCount: Number(form.customerCount || 0), employees: Number(form.employees || 0), industry: getIndustryValue(form), businessType: form.businessTypeCategory === "other" ? form.customBusinessType.trim() : getBusinessTypeLabel(form), businessTypeCategory: form.businessTypeCategory, customBusinessType: form.customBusinessType.trim(), businessDescription: form.description, businessStage: form.businessStage, latitude: form.latitude === "" ? null : Number(form.latitude), longitude: form.longitude === "" ? null : Number(form.longitude) };
      const response = await fetch(`${API}/api/entrepreneur/business-analysis`, { method: "POST", headers, body: JSON.stringify(payload) });
      const data = await response.json().catch(() => null);
      if (!response.ok) throw new Error(data?.detail || "Could not analyse this business.");
      let publicModel = null;
      if (ratios.length === 64) {
        const modelResponse = await fetch(`${API}/api/model/predict`, { method: "POST", headers, body: JSON.stringify({ financialRatios: ratios }) });
        publicModel = await modelResponse.json().catch(() => null);
        if (!modelResponse.ok) throw new Error(publicModel?.detail || "Could not analyse the accounting ratios.");
      }
      let locationAnalysis = null;
      if (form.latitude !== "" && form.longitude !== "" && form.industry.trim()) {
        try {
          const locationResponse = await fetch(`${API}/api/entrepreneur/location-analysis`, { method: "POST", headers, body: JSON.stringify({ latitude: Number(form.latitude), longitude: Number(form.longitude), industry: getIndustryValue(form), businessType: payload.businessType, businessTypeCategory: form.businessTypeCategory, radiusMeters: 1000 }) });
          locationAnalysis = await locationResponse.json().catch(() => null);
          if (!locationResponse.ok) locationAnalysis = { status: "unavailable", verdict: "Location data unavailable", message: locationAnalysis?.detail || "Nearby map data could not be retrieved.", safety: { status: "not_assessed", message: "Safety has not been assessed." } };
        } catch { locationAnalysis = { status: "unavailable", verdict: "Location data unavailable", message: "Could not connect to the nearby map data service.", safety: { status: "not_assessed", message: "Safety has not been assessed." } }; }
      }
      setAnalysis({ ...data, financialRatios: ratios.length === 64 ? ratios : data.financialRatios, publicModel, locationAnalysis });
      setMessage("Business analysis completed. Review the result before publishing.");
    } catch (analysisError) {
      setError(analysisError.message || "Could not analyse this business.");
    } finally {
      setAnalyzing(false);
    }
  }
  if (loading) return <div className="profile-panel" role="status" aria-live="polite">Loading businesses...</div>;
  if (loadError) return <div className="profile-panel" role="alert"><h2>Couldn’t load your businesses</h2><p>{loadError}</p><button type="button" className="secondary-button" onClick={load}>Try again</button></div>;
  return <section className="business-profile-page"><div className="profile-heading"><p className="profile-eyebrow">MY BUSINESSES</p><h1>Business proposals</h1><p>Complete the business details, analyse the numbers, then publish the proposal for funders to review.</p></div><div className="business-switcher">{businesses.map((item) => <button type="button" className={selectedId === item.id ? "selected" : ""} key={item.id} onClick={() => selectBusiness(item)}>{item.businessName}</button>)}<button type="button" className="new-business" onClick={newBusiness}>Add another business</button></div>{message && <div className="profile-message success">{message}</div>}{error && !businessToDelete && <div className="profile-message error">{error}</div>}<form className="profile-panel" onSubmit={save}><h2>{selectedId ? "Edit business proposal" : "New business proposal"}</h2><div className="profile-form-grid"><label>Business name *<input value={form.businessName} onChange={(e) => updateField("businessName", e.target.value)} required /></label><label>Industry sector *<select value={form.industry} onChange={(e) => changeIndustry(e.target.value)} required><option value="">Choose an industry sector</option>{INDUSTRIES.map((industry) => <option key={industry} value={industry}>{industry}</option>)}</select></label>{form.industry === "Other" && <label>Describe the industry sector *<input value={form.customIndustry} onChange={(e) => updateField("customIndustry", e.target.value)} placeholder="For example, renewable energy" required /></label>}<label>Business size / stage *<select value={form.businessStage} onChange={(e) => updateField("businessStage", e.target.value)} required><option value="">Choose the business size / stage</option>{BUSINESS_STAGES.map((stage) => <option key={stage} value={stage}>{stage}</option>)}</select></label><label>What kind of business is it? *<select value={form.businessTypeCategory} onChange={(e) => updateField("businessTypeCategory", e.target.value)} required disabled={!form.industry}><option value="">{form.industry ? "Choose a business type" : "Choose an industry first"}</option>{(BUSINESS_TYPE_GROUPS[form.industry] || []).map(([key, label]) => <option key={key} value={key}>{label}</option>)}</select></label>{form.businessTypeCategory === "other" && <label>Describe the business type *<input value={form.customBusinessType} onChange={(e) => updateField("customBusinessType", e.target.value)} placeholder="Describe the specific business" required /></label>}<div className="full-width"><LocationPicker value={form} onChange={updateLocation} /></div><label className="full-width">Business description *<textarea value={form.description} onChange={(e) => updateField("description", e.target.value)} rows="5" required /></label><label>Funding needed (ZAR)<input type="number" min="0" value={form.fundingNeeded} onChange={(e) => updateField("fundingNeeded", e.target.value)} /></label><label>Intended use of funds<input value={form.intendedUseOfFunds} onChange={(e) => updateField("intendedUseOfFunds", e.target.value)} /></label><label>Expected monthly revenue<input type="number" min="0" value={form.monthlyRevenue} onChange={(e) => updateField("monthlyRevenue", e.target.value)} /></label><label>Expected monthly expenses<input type="number" min="0" value={form.monthlyExpenses} onChange={(e) => updateField("monthlyExpenses", e.target.value)} /></label><label>Expected monthly growth (%)<input type="number" min="0" value={form.monthlyGrowthPercent} onChange={(e) => updateField("monthlyGrowthPercent", e.target.value)} /></label><label>Total assets (ZAR)<input type="number" min="0" value={form.totalAssets} onChange={(e) => updateField("totalAssets", e.target.value)} /></label><label>Total liabilities (ZAR)<input type="number" min="0" value={form.totalLiabilities} onChange={(e) => updateField("totalLiabilities", e.target.value)} /></label><label>Cash on hand (ZAR)<input type="number" min="0" value={form.cashOnHand} onChange={(e) => updateField("cashOnHand", e.target.value)} /></label><label>Current customers<input type="number" min="0" value={form.customerCount} onChange={(e) => updateField("customerCount", e.target.value)} /></label><label>Employees<input type="number" min="0" value={form.employees} onChange={(e) => updateField("employees", e.target.value)} /></label><label className="full-width">Advanced accounting ratios (optional)<textarea value={advancedRatios} onChange={(e) => updateAdvancedRatios(e.target.value)} rows="3" placeholder="Paste exactly 64 comma-separated ratios from your financial statements." /></label></div><div className="profile-form-footer"><button type="button" className="secondary-button" onClick={analyse} disabled={analyzing || saving}>{analyzing ? "Analysing..." : "Analyse business"}</button><button type="submit" disabled={saving || analyzing || !analysis}>{saving ? "Publishing..." : "Publish proposal"}</button>{selectedId && <button type="button" className="danger-button" onClick={() => setBusinessToDelete({ id: selectedId, businessName: form.businessName })}>Delete proposal</button>}</div></form>{(selectedId || analysis || analyzing) && <section className="analysis-box"><p className="profile-eyebrow">BUSINESS ANALYSIS</p><h2>Location evidence and financial estimate</h2><p>Location findings use mapped nearby features. Financial figures below are arithmetic based on your entries, not verified facts or a profit guarantee.</p><button type="button" onClick={analyse} disabled={analyzing || saving}>{analyzing ? "Analysing..." : "Run analysis"}</button>{analyzing && <p role="status">Calculating your business outlook...</p>}{analysis && <div className="analysis-result"><section className="location-analysis-result"><h3>Location evidence for {getBusinessTypeLabel(form)} in {getIndustryValue(form) || "the selected industry"}</h3>{analysis.locationAnalysis ? <>{analysis.locationAnalysis.industryAlignedWithBusinessType === false && <p className="location-type-warning"><strong>Check your selections:</strong> the industry sector and business type may not match.</p>}<strong>{analysis.locationAnalysis.verdict}</strong><p>{analysis.locationAnalysis.message}</p>{analysis.locationAnalysis.status !== "unavailable" && <ul>{analysis.locationAnalysis.nearbyTypeListingsCount != null ? <li>{analysis.locationAnalysis.nearbyTypeListingsCount} nearby named listings matching this business type in the map search</li> : analysis.locationAnalysis.industryMatchSupported !== false && analysis.locationAnalysis.competitorCount != null && <li>{analysis.locationAnalysis.competitorCount} mapped places tagged like this business type within 1 km</li>}{analysis.locationAnalysis.relevantAnchors != null && <li>{analysis.locationAnalysis.relevantAnchors} nearby customer or industry context features counted for this business type</li>}{analysis.locationAnalysis.nearbyTransitFeatures != null && <li>{analysis.locationAnalysis.nearbyTransitFeatures} mapped public transport features</li>}{analysis.locationAnalysis.residentialAreaFeatures != null && <li>{analysis.locationAnalysis.residentialAreaFeatures} residential/neighbourhood features and {analysis.locationAnalysis.nearbyOffices ?? 0} office/commercial features</li>}{analysis.locationAnalysis.nearbyTypeListings?.length > 0 && <li>Closest listings: {analysis.locationAnalysis.nearbyTypeListings.slice(0, 3).map((place) => `${place.name} (${place.distanceMeters} m)`).join("; ")}</li>}</ul>}<small>{analysis.locationAnalysis.source || "Map data"}. {analysis.locationAnalysis.coverageNote || "Map results may be incomplete."} Radius checked: {((analysis.locationAnalysis.radiusMeters || 1000) / 1000).toFixed(1)} km.</small><p className="safety-status"><strong>Safety: Not assessed.</strong> {analysis.locationAnalysis.safety?.message || "This analysis does not determine whether the area is safe."}</p></> : <p>Choose a map location and run the analysis to check nearby mapped activity. Location demand and safety have not been assessed.</p>}</section><section className="financial-estimate"><h3>Financial calculation from your figures</h3><strong>{analysis.outlook}</strong><p>{analysis.summary}</p><p>Monthly surplus or deficit: <strong>R{Number(analysis.estimatedMonthlyProfit || 0).toLocaleString()}</strong></p>{analysis.estimatedBreakEvenMonths != null && <p>Simple startup-cost payback: <strong>{analysis.estimatedBreakEvenMonths} months</strong>, assuming the entered monthly surplus remains unchanged and before unlisted costs.</p>}{analysis.publicModel && <p>Public-model distress estimate: <strong>{analysis.publicModel.riskLevel}</strong> ({Math.round(Number(analysis.publicModel.financialDistressProbability || 0) * 100)}%). This model result is separate from location evidence.</p>}<p className="analysis-disclaimer">{analysis.disclaimer}</p>{analysis.riskFlags?.length > 0 && <ul>{analysis.riskFlags.map((risk) => <li key={risk}>{risk}</li>)}</ul>}</section></div>}</section>}{businessToDelete && <div className="modal-backdrop business-delete-backdrop" onMouseDown={(event) => { if (event.target === event.currentTarget && !deleting) setBusinessToDelete(null); }}><section className="confirm-modal business-delete-modal" role="dialog" aria-modal="true" aria-labelledby="delete-business-title" aria-describedby="delete-business-description"><h2 id="delete-business-title">Delete this proposal?</h2><p id="delete-business-description">Delete <strong>{businessToDelete.businessName || "this business proposal"}</strong>? This can’t be undone.</p>{error && <div className="profile-message error" role="alert">{error}</div>}<div className="modal-actions"><button type="button" className="secondary-button" onClick={() => setBusinessToDelete(null)} disabled={deleting}>Cancel</button><button type="button" className="danger-button" onClick={remove} disabled={deleting}>{deleting ? "Deleting..." : "Delete"}</button></div></section></div>}</section>;
}
