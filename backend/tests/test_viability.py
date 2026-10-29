import unittest

from viability import CATEGORY_WEIGHTS, build_business_viability


BASE = {
    "businessName": "Test business",
    "industry": "Retail",
    "businessType": "Grocery store",
    "businessTypeCategory": "grocery",
    "location": "Rural Limpopo",
    "businessStage": "Operating",
    "startupCosts": 100000,
    "availableCapital": 40000,
    "fundingRequired": 60000,
    "monthlyRevenue": 80000,
    "monthlyExpenses": 60000,
    "customerCount": 80,
    "targetMarket": "Nearby households and commuters",
    "businessExperience": "Five years in retail",
    "operationsPlan": "Local supplier and delivery arrangements are planned.",
    "riskMitigation": "Keep three months of operating cash.",
    "providedInputs": ["startupCosts", "availableCapital", "fundingRequired", "monthlyRevenue", "monthlyExpenses"],
}


class ViabilityAssessmentTests(unittest.TestCase):
    def test_weights_and_score_are_bounded(self):
        self.assertEqual(sum(CATEGORY_WEIGHTS.values()), 100)
        result = build_business_viability(BASE, {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 8, "relevantAnchors": 4, "competitorCount": 2})
        self.assertGreaterEqual(result["score"], 0)
        self.assertLessEqual(result["score"], 100)
        self.assertEqual(sum(category["weight"] for category in result["categoryScores"]), 100)
        self.assertAlmostEqual(sum(category["contribution"] for category in result["categoryScores"]), result["score"], delta=0.5)

    def test_profit_and_margin_calculation(self):
        result = build_business_viability(BASE, {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 8, "relevantAnchors": 4, "competitorCount": 2})
        self.assertEqual(result["financials"]["monthlyProfit"], 20000)
        self.assertEqual(result["financials"]["profitMarginPercent"], 25)
        self.assertEqual(result["financials"]["breakEvenMonths"], 5.0)

    def test_weak_financials_flag_loss_and_funding_gap(self):
        values = {**BASE, "monthlyRevenue": 10000, "monthlyExpenses": 25000, "availableCapital": 10000, "fundingRequired": 10000}
        result = build_business_viability(values, {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 5, "relevantAnchors": 1, "competitorCount": 10})
        self.assertEqual(result["financials"]["monthlyProfit"], -15000)
        self.assertEqual(result["financials"]["fundingGap"], 80000)
        self.assertIn("High risk", result["prediction"])
        self.assertTrue(result["risks"])

    def test_missing_financials_use_neutral_score_and_reduce_confidence(self):
        values = {"businessTypeCategory": "agriculture", "providedInputs": []}
        result = build_business_viability(values, {"status": "partial_data", "contextDataAvailable": False})
        financial = next(item for item in result["categoryScores"] if item["key"] == "financialViability")
        self.assertEqual(financial["score"], 50)
        self.assertEqual(result["financials"]["monthlyProfit"], None)
        self.assertEqual(result["confidence"], "Limited")
        self.assertEqual(result["locationEvidence"]["relevantContextCount"], 0)

    def test_rural_map_gap_is_not_a_negative_location_score(self):
        result = build_business_viability(BASE, {"status": "partial_data", "contextDataAvailable": False})
        location = next(item for item in result["categoryScores"] if item["key"] == "locationMarket")
        self.assertEqual(location["score"], 50)
        self.assertIn("does not count this against", location["explanation"])

    def test_industry_guidance_varies_by_sector(self):
        agriculture = build_business_viability({**BASE, "businessTypeCategory": "agriculture"}, {})
        restaurant = build_business_viability({**BASE, "businessTypeCategory": "restaurant"}, {})
        self.assertIn("water", agriculture["sectorGuidance"]["focus"].lower())
        self.assertIn("food", restaurant["sectorGuidance"]["focus"].lower())


if __name__ == "__main__":
    unittest.main()
