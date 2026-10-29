# FundBridge financial model

The current entrepreneur profitability/viability assessment is a transparent, rules-based baseline in `backend/viability.py`; it is not trained AI. See [`docs/business-viability-assessment.md`](../docs/business-viability-assessment.md) for category weights, connected and considered South African sources, licensing notes, limits, and model-integration requirements.

`train_bankruptcy_model.py` trains a reproducible logistic-regression baseline from the UCI Polish Companies Bankruptcy 5-year dataset. The raw dataset is intentionally ignored from Git; download and extract it to `data/polish_bankruptcy/5year.arff` before retraining.

The artifact is an auxiliary financial-distress signal. It is not a profitability guarantee, live market research, or an automated funding decision. Its features are public-company financial ratios, so it must not be applied directly to a FundBridge proposal until the proposal form collects compatible accounting inputs.

Training command:

```powershell
$py = "C:\Users\Tebogo\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
& $py model/train_bankruptcy_model.py
```
