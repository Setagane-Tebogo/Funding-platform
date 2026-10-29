"""Transparent baseline for FundBridge business viability assessments.

This is a configurable rules-based screening model, not a trained predictor.
Unknown inputs receive neutral scores and reduce data completeness.
"""
from __future__ import annotations

from typing import Any


CATEGORY_WEIGHTS = {
    "locationMarket": 25,
    "industryCompetition": 20,
    "financialViability": 25,
    "capitalAdequacy": 15,
    "operationalReadiness": 10,
    "riskResilience": 5,
}

SECTOR_GUIDANCE = {
    "agriculture": {
        "label": "Agriculture",
        "focus": "Check water, land, climate/seasonality, input costs, storage, and routes to buyers.",
        "missing": ["water and land access", "seasonal production and input-cost plan", "buyer or distribution arrangements"],
    },
    "farm_supply": {
        "label": "Agricultural supplies",
        "focus": "Check nearby farming activity, supplier lead times, seasonal demand, and delivery routes.",
        "missing": ["supplier and delivery plan", "local farmer/customer validation", "seasonal stock plan"],
    },
    "grocery": {
        "label": "Retail / grocery",
        "focus": "Check customer access, local purchasing power, stock margins, supplier costs, and nearby alternatives.",
        "missing": ["customer and price validation", "supplier quotes and stock margins", "local purchasing-power evidence"],
    },
    "clothing": {
        "label": "Retail / clothing",
        "focus": "Check target-customer fit, stock turnover, margins, online reach, and nearby alternatives.",
        "missing": ["customer and price validation", "supplier quotes and expected stock turnover"],
    },
    "electronics": {
        "label": "Retail / electronics",
        "focus": "Check stock financing, supplier reliability, repair/warranty costs, customer access, and competition.",
        "missing": ["supplier and warranty-cost estimates", "customer and price validation"],
    },
    "restaurant": {
        "label": "Food services",
        "focus": "Check foot access, food and packaging costs, rent, food safety, delivery options, and nearby alternatives.",
        "missing": ["menu costing and supplier quotes", "customer/footfall validation", "food-safety and delivery plan"],
    },
    "cafe": {
        "label": "Food services",
        "focus": "Check customer access, ingredient costs, rent, opening hours, and nearby alternatives.",
        "missing": ["menu costing and supplier quotes", "customer/footfall validation"],
    },
    "bakery": {
        "label": "Food production / retail",
        "focus": "Check ingredient and energy costs, production capacity, freshness/waste, and buyer routes.",
        "missing": ["ingredient and energy cost estimates", "daily buyer or order validation"],
    },
    "catering": {
        "label": "Food services",
        "focus": "Check confirmed event/customer pipeline, food costs, delivery logistics, and seasonality.",
        "missing": ["confirmed orders or customer pipeline", "supplier and delivery quotes"],
    },
    "manufacturing": {
        "label": "Manufacturing",
        "focus": "Check raw-material suppliers, equipment and power needs, production costs, logistics, and confirmed demand.",
        "missing": ["equipment and utility requirements", "supplier quotes", "orders or customer validation"],
    },
    "construction": {
        "label": "Construction / trades",
        "focus": "Check a verified project pipeline, materials, skills/certifications, travel costs, and payment terms.",
        "missing": ["quotes or project pipeline", "materials and transport costs", "required skills/certifications"],
    },
    "professional": {
        "label": "Professional / technology services",
        "focus": "Check reachable clients, customer acquisition costs, recurring revenue, connectivity, and delivery capacity.",
        "missing": ["client pipeline or paid trials", "customer acquisition and delivery costs"],
    },
    "health": {
        "label": "Health and care",
        "focus": "Check patient/community need, licensing, qualified staff, supply continuity, and access to services.",
        "missing": ["licensing and staffing requirements", "service-demand validation", "medicine/equipment supply plan"],
    },
    "education": {
        "label": "Education and childcare",
        "focus": "Check learner/parent demand, registration requirements, staffing, safety, and access routes.",
        "missing": ["registration and safeguarding requirements", "learner/parent demand validation", "staffing plan"],
    },
    "tourism": {
        "label": "Tourism and accommodation",
        "focus": "Check seasonal visitor demand, booking channels, transport access, occupancy assumptions, and operating costs.",
        "missing": ["booking evidence and seasonality", "occupancy and operating-cost assumptions", "visitor access plan"],
    },
    "travel": {
        "label": "Tourism and travel",
        "focus": "Check customer pipeline, supplier/operator agreements, seasonality, and transport arrangements.",
        "missing": ["customer bookings or pipeline", "supplier/operator agreements", "seasonal cash-flow plan"],
    },
    "automotive": {
        "label": "Automotive services",
        "focus": "Check vehicle access, parts supply, equipment, skills, fuel/travel costs, and customer demand.",
        "missing": ["equipment and skills plan", "parts supplier quotes", "customer demand validation"],
    },
    "carwash": {
        "label": "Vehicle services",
        "focus": "Check vehicle access, water supply, wastewater rules, consumables, and repeat-customer demand.",
        "missing": ["water and wastewater arrangements", "site access and customer validation"],
    },
    "transport": {
        "label": "Passenger transport",
        "focus": "Check local passenger routes, permits, vehicle finance, fuel, maintenance, and passenger demand.",
        "missing": ["route and permit checks", "vehicle, fuel, and maintenance costs", "passenger demand validation"],
    },
    "logistics": {
        "label": "Delivery and logistics",
        "focus": "Check route density, fuel and vehicle costs, delivery contracts, dispatch capacity, and connectivity.",
        "missing": ["customer contracts or delivery pipeline", "route and fuel costs", "vehicle maintenance and connectivity plan"],
    },
    "other": {
        "label": "Other business",
        "focus": "Validate target customers, pricing, suppliers, delivery costs, and relevant operating requirements.",
        "missing": ["specific customer and pricing evidence", "supplier and delivery plan", "industry-specific operating requirements"],
    },
}

CATEGORY_ALIASES = {"bakery": "grocery", "catering": "restaurant", "training": "education", "accommodation": "tourism", "accounting": "professional", "legal": "professional"}

SECTOR_OPERATIONS_TERMS = {
    "agriculture": ("water", "land", "season", "climate", "input", "buyer", "market", "irrigation", "storage"),
    "farm_supply": ("supplier", "farmer", "season", "delivery", "stock", "input"),
    "grocery": ("supplier", "stock", "margin", "price", "delivery", "customer"),
    "clothing": ("supplier", "stock", "turnover", "margin", "customer", "online"),
    "electronics": ("supplier", "warranty", "repair", "stock", "customer"),
    "restaurant": ("food", "ingredient", "hygiene", "delivery", "rent", "menu", "supplier"),
    "cafe": ("ingredient", "hygiene", "delivery", "rent", "menu", "supplier"),
    "bakery": ("ingredient", "energy", "production", "waste", "buyer", "supplier"),
    "catering": ("order", "event", "food", "delivery", "supplier", "season"),
    "manufacturing": ("equipment", "material", "power", "energy", "production", "logistics", "order", "supplier"),
    "construction": ("project", "material", "skill", "certification", "transport", "payment"),
    "professional": ("client", "internet", "acquisition", "recurring", "delivery", "software"),
    "health": ("license", "staff", "supply", "medicine", "equipment", "patient"),
    "education": ("registration", "staff", "safety", "learner", "parent", "transport"),
    "tourism": ("season", "booking", "occupancy", "visitor", "transport", "cost"),
    "travel": ("booking", "season", "operator", "supplier", "transport"),
    "automotive": ("equipment", "skill", "parts", "supplier", "fuel", "customer"),
    "carwash": ("water", "wastewater", "site", "customer", "consumable"),
    "transport": ("route", "permit", "vehicle", "fuel", "maintenance", "passenger"),
    "logistics": ("route", "fuel", "vehicle", "delivery", "contract", "dispatch", "internet"),
}

SECTOR_RISK_TERMS = {
    "agriculture": ("season", "weather", "drought", "water", "insurance", "backup", "reserve", "crop"),
    "farm_supply": ("season", "supplier", "backup", "reserve", "stock"),
    "restaurant": ("supplier", "backup", "food", "waste", "reserve", "insurance"),
    "cafe": ("supplier", "backup", "food", "waste", "reserve"),
    "manufacturing": ("power", "backup", "supplier", "maintenance", "reserve", "insurance"),
    "transport": ("fuel", "maintenance", "insurance", "backup", "reserve", "vehicle"),
    "logistics": ("fuel", "maintenance", "insurance", "backup", "reserve", "vehicle"),
}


def _clamp(value: float, low: float = 0, high: float = 100) -> float:
    return max(low, min(high, value))


def _present(values: dict[str, Any], name: str) -> bool:
    provided = values.get("providedInputs")
    if isinstance(provided, list):
        return name in provided
    value = values.get(name)
    return value is not None and value != ""


def build_business_viability(values: dict[str, Any], location: dict[str, Any], experience_fallback: str = "") -> dict[str, Any]:
    """Return a weighted, explainable assessment from supplied inputs and OSM context."""
    category = str(values.get("businessTypeCategory") or "other").lower()
    industry_text = str(values.get("industry") or "").casefold()
    sector_key = CATEGORY_ALIASES.get(category, category)
    if sector_key == "other":
        industry_sectors = (("agri", "agriculture"), ("farm", "agriculture"), ("retail", "grocery"), ("food", "restaurant"), ("hospital", "restaurant"), ("manufactur", "manufacturing"), ("trade", "construction"), ("transport", "transport"), ("logistic", "logistics"), ("tourism", "tourism"), ("education", "education"), ("health", "health"), ("automotive", "automotive"), ("professional", "professional"), ("technology", "professional"))
        sector_key = next((mapped for keyword, mapped in industry_sectors if keyword in industry_text), "other")
    sector = SECTOR_GUIDANCE.get(sector_key, SECTOR_GUIDANCE["other"])
    revenue = float(values.get("monthlyRevenue") or 0)
    expenses = float(values.get("monthlyExpenses") or 0)
    startup = float(values.get("startupCosts") or 0)
    available = float(values.get("availableCapital") or 0)
    funding = float(values.get("fundingRequired") or 0)
    customer_count = int(values.get("customerCount") or 0)
    competitors = int(location.get("competitorCount") or location.get("nearbyTypeListingsCount") or 0)
    anchors = int(location.get("relevantAnchors") or 0)
    mapped_features = int(location.get("mappedFeatureCount") or 0)
    radius_meters = int(location.get("radiusMeters") or 5000)
    map_available = location.get("status") not in {None, "unavailable"}
    map_context = bool(
        map_available
        and location.get("contextDataAvailable") is not False
        and mapped_features > 0
        and location.get("status") != "limited_data"
    )
    target_market = str(values.get("targetMarket") or "").strip()
    experience = str(values.get("businessExperience") or experience_fallback or "").strip()
    operations_plan = str(values.get("operationsPlan") or "").strip()
    risk_mitigation = str(values.get("riskMitigation") or "").strip()
    stage = str(values.get("businessStage") or "").casefold()
    industry_aligned = location.get("industryAlignedWithBusinessType") is not False

    # Location is based on pin-specific mapped context: local activity density, relevant
    # anchors, and transit access raise the score; dense same-type competition lowers it.
    # Sparse/unavailable data stays neutral, especially for rural areas. OSM does not prove
    # customer demand, purchasing power, safety, or infrastructure reliability.
    if not map_context:
        if map_available and competitors > 0:
            competition_adjustment = -15 if competitors >= 8 else -7 if competitors >= 4 else 3
            location_score = _clamp(50 + competition_adjustment)
            location_reason = (
                f"The location lookup returned {competitors} named listing(s) matching this business type, "
                "which provides a limited competition signal for this pin. Nearby customer activity and access "
                "could not be verified, so the score reflects competition only; incomplete rural or urban map "
                "coverage is not proof of low demand."
            )
        else:
            location_score = 50
            location_reason = "Reliable nearby map context was unavailable or too sparse, so location remains neutral; missing map data does not count this against urban or rural locations. The score cannot infer local demand without mapped evidence."
    else:
        transit = int(location.get("nearbyTransitFeatures") or 0)
        density_points = min(15, max(0, (mapped_features - 4) // 10 * 3))
        anchor_points = min(20, anchors * 4)
        access_points = min(10, transit * 2)
        competition_adjustment = -15 if competitors >= 8 else -7 if competitors >= 4 else 3 if competitors > 0 else 0
        location_score = _clamp(50 + density_points + anchor_points + access_points + competition_adjustment)
        location_reason = (
            f"Within {radius_meters:,} m of this pin, OpenStreetMap returned {mapped_features} mapped feature(s), including "
            f"{anchors} context anchor(s) relevant to {values.get('businessType') or 'this business type'} "
            f"and {transit} transit feature(s). {competitors} similar mapped business(es) "
            f"{'lower the location score because of a competition signal' if competitors >= 4 else 'provide a limited market-presence signal' if competitors else 'were returned'}; "
            "these map indicators are incomplete proxies, not customer counts, spending data, or proof of profit."
        )
    if not industry_aligned:
        location_score = min(location_score, 30)
        location_reason += " The selected industry and business type may not match."

    market_score = 50
    market_reasons = []
    if target_market:
        market_score += 12
        market_reasons.append("A target customer group is described.")
    if customer_count > 0:
        market_score += 8
        market_reasons.append(f"{customer_count} existing customer(s) were reported.")
    if competitors:
        if competitors <= 3:
            market_score += 5
            market_reasons.append(f"{competitors} similar mapped business(es) may indicate an established category as well as competition.")
        elif competitors <= 7:
            market_reasons.append(f"{competitors} similar mapped businesses create a competition signal; demand and competitor strength remain unverified.")
        else:
            market_score -= 15
            market_reasons.append(f"{competitors} similar mapped businesses may make differentiation harder; map counts do not measure their strength.")
    else:
        market_reasons.append("No similar mapped business was returned; this does not prove demand is absent or an opportunity exists.")
    market_score = _clamp(market_score)

    financial_provided = _present(values, "monthlyRevenue") and _present(values, "monthlyExpenses")
    monthly_profit = revenue - expenses
    profit_margin = (monthly_profit / revenue) if revenue > 0 and financial_provided else None
    if not financial_provided:
        financial_score = 50
        financial_reason = "Revenue or expense information is missing; a neutral score is used until both are supplied."
    elif revenue <= 0:
        financial_score = 20 if expenses > 0 else 45
        financial_reason = "No monthly revenue is entered; profit potential cannot be established from the current figures."
    else:
        financial_score = _clamp(50 + float(profit_margin) * 125)
        financial_reason = f"Entered figures show monthly {'profit' if monthly_profit > 0 else 'loss' if monthly_profit < 0 else 'break-even'} of R{monthly_profit:,.2f} and a {float(profit_margin) * 100:.1f}% margin before tax and unlisted costs."

    capital_complete = _present(values, "startupCosts") and _present(values, "availableCapital") and _present(values, "fundingRequired")
    funding_gap = max(0.0, startup - available - funding)
    if startup <= 0 or not capital_complete:
        capital_score = 50
        capital_reason = "Startup cost, available capital, or requested funding is missing; funding adequacy is not yet clear."
    else:
        covered = (available + funding) / startup if startup else 0
        capital_score = 85 if covered >= 1 else 65 if covered >= 0.75 else 45 if covered >= 0.5 else 25
        capital_reason = f"Available capital plus requested funding covers about {min(covered, 5) * 100:.0f}% of startup costs; estimated funding gap R{funding_gap:,.2f}."

    operating = 50
    operating_reasons = []
    if any(word in stage for word in ("operat", "growth", "expand", "establish")):
        operating += 15
        operating_reasons.append("The selected stage indicates an operating or expanding business.")
    elif any(word in stage for word in ("idea", "start")):
        operating -= 5
        operating_reasons.append("The business is at an early stage, so customer validation and an execution plan matter more.")
    if experience:
        operating += 15
        operating_reasons.append("Relevant business experience was provided or found in the entrepreneur profile.")
    if operations_plan:
        operation_terms = SECTOR_OPERATIONS_TERMS.get(sector_key, ())
        operation_matches = [term for term in operation_terms if term in operations_plan.casefold()]
        operating += 5 + min(10, len(operation_matches) * 2) if operation_terms else 10
        if operation_matches:
            operating_reasons.append("The operations plan mentions sector checks: " + ", ".join(operation_matches[:5]) + ".")
        else:
            operating_reasons.append("An operations plan was supplied; check it against the sector-specific requirements.")
    if not operating_reasons:
        operating_reasons.append("Stage, relevant experience, and operating-plan details are limited.")
    operational_score = _clamp(operating)

    resilience_score = 50
    resilience_reasons = []
    if _present(values, "availableCapital") and expenses > 0 and available > 0:
        runway = available / expenses
        resilience_score += 20 if runway >= 3 else 5 if runway >= 1 else -15
        resilience_reasons.append(f"Available capital covers about {runway:.1f} months of entered operating expenses.")
    if risk_mitigation:
        risk_terms = SECTOR_RISK_TERMS.get(sector_key, ())
        risk_matches = [term for term in risk_terms if term in risk_mitigation.casefold()]
        resilience_score += 5 + min(10, len(risk_matches) * 2) if risk_terms else 15
        if risk_matches:
            resilience_reasons.append("The contingency notes mention sector risks: " + ", ".join(risk_matches[:5]) + ".")
        else:
            resilience_reasons.append("A contingency plan was described; verify it addresses the main risks for this sector.")
    if not resilience_reasons:
        resilience_reasons.append("Cash runway and risk-contingency information are limited.")
    resilience_score = _clamp(resilience_score)

    raw_scores = {
        "locationMarket": (location_score, location_reason),
        "industryCompetition": (market_score, " ".join(market_reasons)),
        "financialViability": (financial_score, financial_reason),
        "capitalAdequacy": (capital_score, capital_reason),
        "operationalReadiness": (operational_score, " ".join(operating_reasons)),
        "riskResilience": (resilience_score, " ".join(resilience_reasons)),
    }
    categories = []
    for key, weight in CATEGORY_WEIGHTS.items():
        score, explanation = raw_scores[key]
        categories.append({"key": key, "name": {
            "locationMarket": "Location and local market potential",
            "industryCompetition": "Industry demand and competition",
            "financialViability": "Financial viability and profit margins",
            "capitalAdequacy": "Capital adequacy and funding requirements",
            "operationalReadiness": "Operational readiness and business experience",
            "riskResilience": "Risk management and resilience",
        }[key], "weight": weight, "score": round(score), "contribution": round(score * weight / 100, 2), "explanation": explanation})
    overall = max(0, min(100, round(sum(item["contribution"] for item in categories))))
    band = "Strong potential" if overall >= 80 else "Promising, with areas to improve" if overall >= 65 else "Moderate potential, significant risks present" if overall >= 50 else "High risk" if overall >= 30 else "Very high risk"

    missing = []
    field_checks = [
        (financial_provided, "Expected monthly revenue and expenses"),
        (capital_complete, "Startup costs, available capital, and funding required"),
        (bool(target_market), "Target customers and local demand evidence"),
        (bool(experience), "Relevant owner or team experience"),
        (bool(operations_plan), "Supplier, infrastructure, and delivery plan where relevant"),
        (bool(risk_mitigation), "Risk-contingency plan"),
        (map_context, "Reliable surrounding-area map data"),
    ]
    missing.extend(label for supplied, label in field_checks if not supplied)
    sector_missing = sector["missing"] if not operations_plan else []
    if sector_missing:
        missing.append("Industry-specific checks: " + ", ".join(sector_missing))
    completed = sum(1 for supplied, _ in field_checks if supplied)
    completeness = round(completed * 100 / len(field_checks))
    confidence = "Moderate" if completeness >= 70 and map_context else "Limited" if completeness < 40 or not map_context else "Low"

    if financial_provided and monthly_profit < 0:
        prediction = "High risk of not becoming profitable"
    elif financial_provided and monthly_profit == 0:
        prediction = "High risk of not becoming profitable"
    elif location_score < 40 and market_score < 40:
        prediction = "High risk of not becoming profitable"
    elif overall >= 80 and financial_provided and monthly_profit > 0:
        prediction = "Likely to be profitable"
    elif overall < 50:
        prediction = "High risk of not becoming profitable"
    else:
        prediction = "Potentially profitable with improvements"

    strengths = []
    risks = []
    recommendations = []
    if map_context and anchors:
        strengths.append(f"Mapped local context includes {anchors} feature(s) relevant to this business type.")
    if customer_count:
        strengths.append(f"The business reports {customer_count} existing customer(s).")
    if financial_provided and monthly_profit > 0:
        strengths.append("Entered monthly revenue exceeds entered monthly expenses.")
    if capital_complete and funding_gap == 0:
        strengths.append("Entered available capital and requested funding cover the entered startup costs.")
    if financial_provided and monthly_profit <= 0:
        risks.append("Entered expenses meet or exceed the entered monthly revenue.")
        recommendations.append("Recheck pricing, sales volume, and all monthly costs; validate prices with suppliers and customers.")
    if funding_gap > 0:
        risks.append(f"The entered capital and funding leave a startup-cost gap of R{funding_gap:,.2f}.")
        recommendations.append("Reduce setup costs, stage the launch, or identify a confirmed source for the funding gap.")
    if competitors >= 8:
        risks.append("Several similar mapped businesses appear nearby; their quality and actual market share are unknown.")
        recommendations.append("Interview local customers and compare competitors’ prices, opening hours, and service gaps.")
    if not map_context:
        risks.append("Surrounding map data is limited; rural and unmapped places may be missing.")
        recommendations.append("Validate the site in person with local residents, customers, suppliers, and transport operators.")
    if not target_market:
        recommendations.append("Describe the target customers and collect evidence such as paid trials, pre-orders, or written customer commitments.")
    if not operations_plan:
        recommendations.append("Add sector-specific supplier, infrastructure, and delivery cost checks before committing capital.")
    if not experience:
        recommendations.append("Document relevant owner/team experience or name the training and support needed.")
    if not recommendations:
        recommendations.append("Test the assumptions with paying customers and keep monthly sales and cost records before expanding.")
    if not strengths:
        strengths.append("No strong supporting evidence was supplied yet; add verifiable customer, financial, or operating evidence.")

    startup_payback_months = round(startup / monthly_profit, 1) if financial_provided and startup > 0 and monthly_profit > 0 else None
    sources = [{"name": "OpenStreetMap contributors", "status": "connected" if map_context else "partial" if map_available else "unavailable", "license": "ODbL 1.0", "url": "https://www.openstreetmap.org/copyright", "limitation": "Community-mapped features; incomplete coverage; not a population, purchasing-power, safety, or customer-demand dataset."},
               {"name": "Statistics South Africa Census 2022", "status": "not_connected", "url": "https://www.statssa.gov.za/?page_id=1854", "limitation": "Municipal/census information is not currently joined to this pin; no local population or income estimate is claimed."},
               {"name": "National Treasury Municipal Money API", "status": "not_connected", "url": "https://municipaldata.treasury.gov.za/docs", "limitation": "Municipal finance context is not business-level household purchasing power and is not currently joined to this assessment."}]

    return {
        "model": "FundBridge transparent baseline v1",
        "modelType": "rules_based_not_trained_predictor",
        "businessName": values.get("businessName") or "",
        "industry": values.get("industry") or "",
        "businessType": values.get("businessType") or "",
        "businessTypeCategory": category,
        "location": values.get("location") or "",
        "businessStage": values.get("businessStage") or "",
        "score": overall,
        "band": band,
        "prediction": prediction,
        "predictionDisclaimer": "Indicative screening result, not a statistical probability or guarantee of profitability.",
        "categoryScores": categories,
        "financials": {"monthlyRevenue": revenue if _present(values, "monthlyRevenue") else None, "monthlyExpenses": expenses if _present(values, "monthlyExpenses") else None, "monthlyProfit": monthly_profit if financial_provided else None, "profitMarginPercent": round(profit_margin * 100, 2) if profit_margin is not None else None, "startupCosts": startup if _present(values, "startupCosts") else None, "availableCapital": available if _present(values, "availableCapital") else None, "fundingRequired": funding if _present(values, "fundingRequired") else None, "fundingGap": round(funding_gap, 2) if capital_complete else None, "breakEvenMonths": startup_payback_months},
        "sectorGuidance": sector,
        "locationEvidence": {"status": location.get("status", "unavailable"), "score": round(location_score), "scoreWeight": CATEGORY_WEIGHTS["locationMarket"], "source": location.get("source", "OpenStreetMap services"), "radiusMeters": location.get("radiusMeters"), "mappedFeatureCount": mapped_features if map_available else None, "similarBusinessCount": competitors if map_available else None, "relevantContextCount": anchors if map_available else None, "summary": location_reason, "coverageNote": location.get("coverageNote", "Nearby map data could not be retrieved; no live local statistics are available.")},
        "strengths": strengths,
        "risks": risks,
        "recommendations": list(dict.fromkeys(recommendations)),
        "missingInformation": list(dict.fromkeys(missing)),
        "dataCompletenessPercent": completeness,
        "confidence": confidence,
        "confidenceNote": "Financial and experience information is self-reported. Map evidence is community-maintained. No linked South African demographic, income, utility-reliability, or business-register dataset is available in this assessment.",
        "dataSources": sources,
        "createdAt": None,
    }
