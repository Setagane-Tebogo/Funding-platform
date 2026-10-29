# FundBridge business viability assessment

## Current model and data

FundBridge uses the FastAPI service in `backend/main_fastapi.py`. The viability rubric lives in `backend/viability.py` so it can be tested independently. The React workflow is in `frontend/src/BusinessProfile.jsx` and `frontend/src/BusinessProfile.css`. Assessments are stored in `business_assessments`; the newest result is also attached to the existing business profile for the normal profile/funder view. The history endpoint filters by the authenticated entrepreneur and verifies ownership of any requested profile.

This is a transparent rules-based baseline, not a trained profitability predictor. `model/proposal_outcomes.csv` currently contains only its header, and `model/train_proposal_model.py` requires at least 50 real labelled outcomes and both classes. Do not train on generated outcomes. The existing bankruptcy artifact uses Polish listed-company financial ratios and is not used to predict South African small-business success.

The 100-point weights are configured in `backend/viability.py`: local market/location 25, industry demand/competition 20, financial viability 25, capital adequacy 15, operational readiness/experience 10, and resilience 5. Each category is scored 0–100, and its weighted contribution is shown in the UI. Missing information receives a neutral score for that factor and lowers data completeness/confidence; it is not silently interpreted as positive evidence.

## Connected source

- **OpenStreetMap contributors**: the connected source for nearby named businesses, settlement/land-use context, amenities, and mapped transport. Data is community-maintained under ODbL 1.0 and needs attribution. Coverage is uneven, especially in rural areas. Counts are not population, customer counts, foot traffic, purchasing power, business quality, infrastructure reliability, or safety. The interface presents source and coverage limits. [OpenStreetMap copyright and licence](https://www.openstreetmap.org/copyright).

## South African sources considered, not currently integrated

- **Statistics South Africa Census 2022**: official municipal population and household indicators are useful for future market context. The current service does not join a municipal/census area to the chosen pin, so it makes no local population or income claims. Stats SA's municipal fact sheet terms require attribution and state that the data or reprocessed versions may not be sold without prior permission; confirm applicable permission and exact dataset terms before using them in a commercial product. [Census 2022 municipal fact sheet](https://census.statssa.gov.za/assets/documents/2022/Census_2022_Municipal_factsheet-Web.pdf), [Stats SA Census resources](https://isibaloweb.statssa.gov.za/pages/surveys/pss/censuses/censusp.php).
- **National Treasury Municipal Money API**: its API provides municipality-level financial performance and infrastructure/grant context, not household purchasing power or the health of an individual business. Data completeness depends on municipal submissions, and API usage is subject to its terms. It is not currently queried by the app. [API documentation and terms](https://municipaldata.treasury.gov.za/docs).
- **Municipal open-data portals**: some municipalities publish planning, infrastructure, and community-facility datasets, but coverage and licensing differ by municipality. A future provider should include municipality, dataset version/date, licence, source URL, and missing-coverage indicators before those values affect scores.

## Interpretation and future model integration

The output is a screening assessment, not a funding decision, success probability, or guarantee. `prediction` is an indicative category derived from the weighted score and supplied profit figures. Confidence is capped at moderate while local demand and finances remain self-reported or community-mapped. Sector guidance changes the checks and missing-information prompts by business type; it does not invent industry sales statistics.

To add a trained model, collect consented/anonymised FundBridge outcomes with time-based labels, measure class balance and performance on a held-out cohort, calibrate estimates, check bias and drift, and keep the model's result separate from the rules-based score until validated for South African SMEs and relevant sectors. Never use the current Polish public-company model as a proxy.
