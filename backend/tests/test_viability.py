import unittest

from viability import CATEGORY_WEIGHTS, build_business_viability, classify_settlement


BASE = {
    "businessName": "Test business",
    "industry": "Retail",
    "businessType": "Grocery store",
    "businessTypeCategory": "grocery",
    "location": "Rural Limpopo",
    "businessStage": "Operating",
    "startupCosts": 100000,
    "availableCapital": 100000,
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
        self.assertLessEqual(result["score"], 39)

    def test_positive_location_cannot_hide_a_monthly_loss(self):
        values = {**BASE, "monthlyRevenue": 100000, "monthlyExpenses": 125000}
        strong_location = {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 200, "relevantAnchors": 10, "nearbyTransitFeatures": 10, "competitorCount": 0}
        result = build_business_viability(values, strong_location)
        self.assertLessEqual(result["score"], 39)
        self.assertGreater(result["weightedScoreBeforeRiskAdjustments"], result["score"])
        self.assertIn(result["band"], {"High risk", "Very high risk"})
        self.assertIn("higher than revenue", result["scoreAdjustment"]["reasons"][0])

    def test_break_even_and_underfunded_projections_receive_score_limits(self):
        break_even = build_business_viability({**BASE, "monthlyRevenue": 50000, "monthlyExpenses": 50000}, {})
        underfunded = build_business_viability({**BASE, "availableCapital": 1000, "fundingRequired": 1000}, {})
        self.assertLessEqual(break_even["score"], 49)
        self.assertLessEqual(underfunded["score"], 59)
        self.assertTrue(break_even["scoreAdjustment"]["applied"])
        self.assertTrue(underfunded["scoreAdjustment"]["applied"])

    def test_missing_monthly_financials_cannot_receive_a_strong_score(self):
        values = {**BASE, "providedInputs": ["startupCosts", "availableCapital", "fundingRequired"]}
        strong_location = {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 200, "relevantAnchors": 10, "nearbyTransitFeatures": 10, "competitorCount": 0}
        result = build_business_viability(values, strong_location)
        self.assertLessEqual(result["score"], 64)
        self.assertTrue(result["scoreAdjustment"]["applied"])
        self.assertIn("incomplete", result["scoreAdjustment"]["reasons"][0])

    def test_zero_expenses_do_not_produce_a_strong_profitability_score(self):
        values = {**BASE, "monthlyRevenue": 90000, "monthlyExpenses": 0}
        result = build_business_viability(values, {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 200, "relevantAnchors": 10, "nearbyTransitFeatures": 10, "competitorCount": 0})
        self.assertLessEqual(result["score"], 49)
        self.assertIn("No monthly expenses were entered", " ".join(result["scoreAdjustment"]["reasons"]))
        self.assertTrue(any("No monthly operating expenses" in risk for risk in result["risks"]))

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

    def test_location_and_business_type_change_the_score(self):
        weak_location = {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 24, "relevantAnchors": 0, "nearbyTransitFeatures": 0, "competitorCount": 12}
        strong_location = {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 24, "relevantAnchors": 6, "nearbyTransitFeatures": 4, "competitorCount": 1}
        weak = build_business_viability(BASE, weak_location)
        strong = build_business_viability(BASE, strong_location)
        weak_score = next(item["score"] for item in weak["categoryScores"] if item["key"] == "locationMarket")
        strong_score = next(item["score"] for item in strong["categoryScores"] if item["key"] == "locationMarket")
        self.assertLess(weak_score, strong_score)
        self.assertLess(weak["score"], strong["score"])
        self.assertIn("competition signal", next(item["explanation"] for item in weak["categoryScores"] if item["key"] == "locationMarket"))

    def test_partial_place_search_still_changes_location_score_on_competition_evidence(self):
        few_listings = build_business_viability(BASE, {"status": "partial_geocoder", "contextDataAvailable": False, "nearbyTypeListingsCount": 2})
        many_listings = build_business_viability(BASE, {"status": "partial_geocoder", "contextDataAvailable": False, "nearbyTypeListingsCount": 9})
        few_score = next(item["score"] for item in few_listings["categoryScores"] if item["key"] == "locationMarket")
        many_score = next(item["score"] for item in many_listings["categoryScores"] if item["key"] == "locationMarket")
        self.assertGreater(few_score, many_score)
        self.assertIn("competition signal", many_listings["locationEvidence"]["summary"])

    def test_mapped_activity_density_changes_location_and_overall_scores(self):
        low_activity = build_business_viability(BASE, {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 8, "relevantAnchors": 1, "nearbyTransitFeatures": 0, "competitorCount": 0})
        high_activity = build_business_viability(BASE, {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 80, "relevantAnchors": 1, "nearbyTransitFeatures": 0, "competitorCount": 0})
        low_location = next(item["score"] for item in low_activity["categoryScores"] if item["key"] == "locationMarket")
        high_location = next(item["score"] for item in high_activity["categoryScores"] if item["key"] == "locationMarket")
        self.assertGreater(high_location, low_location)
        self.assertGreater(high_activity["score"], low_activity["score"])

    def test_sparse_map_evidence_changes_score_without_claiming_full_confidence(self):
        sparse = build_business_viability(BASE, {"status": "limited_data", "contextDataAvailable": True, "mappedFeatureCount": 1, "relevantAnchors": 1, "nearbyTransitFeatures": 0, "competitorCount": 0})
        no_data = build_business_viability(BASE, {"status": "unavailable", "contextDataAvailable": False})
        sparse_location = next(item["score"] for item in sparse["categoryScores"] if item["key"] == "locationMarket")
        no_data_location = next(item["score"] for item in no_data["categoryScores"] if item["key"] == "locationMarket")
        self.assertGreater(sparse_location, no_data_location)
        self.assertEqual(sparse["confidence"], "Limited")
        self.assertIn("sparse evidence", sparse["locationEvidence"]["summary"])

    def test_settlement_type_fallback_changes_score_by_industry(self):
        rural_site = build_business_viability(BASE, {"status": "partial_location", "contextDataAvailable": False, "settlementClass": "rural", "localityLabel": "Mokopane outskirts"})
        town_site = build_business_viability(BASE, {"status": "partial_location", "contextDataAvailable": False, "settlementClass": "urban_or_town", "localityLabel": "Polokwane"})
        rural_location = next(item["score"] for item in rural_site["categoryScores"] if item["key"] == "locationMarket")
        town_location = next(item["score"] for item in town_site["categoryScores"] if item["key"] == "locationMarket")
        self.assertNotEqual(rural_location, town_location)
        self.assertIn("does not measure local demand", rural_site["locationEvidence"]["summary"])

    def test_settlement_classifier_handles_town_and_rural_labels(self):
        self.assertEqual(classify_settlement({"town": "Polokwane"}, "suburb"), ("urban_or_town", "Polokwane"))
        self.assertEqual(classify_settlement({"village": "Ga-Matlala"}, "village"), ("rural", "Ga-Matlala"))
        self.assertEqual(classify_settlement({}, "road"), ("unknown", ""))

    def test_supported_locality_profiles_are_repeatable_and_business_specific(self):
        polokwane = build_business_viability({**BASE, "location": "Polokwane, Limpopo"}, {"status": "partial_location", "contextDataAvailable": False, "settlementClass": "urban_or_town", "localityLabel": "Polokwane"})
        polokwane_repeat = build_business_viability({**BASE, "location": "Polokwane, Limpopo"}, {"status": "partial_location", "contextDataAvailable": False, "settlementClass": "urban_or_town", "localityLabel": "Polokwane"})
        tzaneen = build_business_viability({**BASE, "location": "Tzaneen, Limpopo"}, {"status": "partial_location", "contextDataAvailable": False, "settlementClass": "urban_or_town", "localityLabel": "Tzaneen"})
        location_score = lambda result: next(item["score"] for item in result["categoryScores"] if item["key"] == "locationMarket")
        self.assertEqual(location_score(polokwane), location_score(polokwane_repeat))
        self.assertNotEqual(location_score(polokwane), location_score(tzaneen))
        self.assertNotEqual(polokwane["score"], tzaneen["score"])
        self.assertEqual(polokwane["locationEvidence"]["localityProfileAdjustment"], 6)
        self.assertEqual(tzaneen["locationEvidence"]["localityProfileAdjustment"], 1)
        self.assertIn("published regional role", polokwane["locationEvidence"]["summary"])
        self.assertEqual(polokwane["locationEvidence"]["localityProfileSource"]["name"], "Limpopo Provincial Government Annual Performance Plan 2023/24")

    def test_same_locality_uses_different_sector_context(self):
        polokwane_retail = build_business_viability({**BASE, "businessTypeCategory": "grocery"}, {"localityLabel": "Polokwane"})
        tzaneen_agriculture = build_business_viability({**BASE, "businessTypeCategory": "agriculture"}, {"localityLabel": "Tzaneen"})
        self.assertEqual(polokwane_retail["locationEvidence"]["localityProfileAdjustment"], 6)
        self.assertEqual(tzaneen_agriculture["locationEvidence"]["localityProfileAdjustment"], 6)

    def test_locality_from_submitted_location_applies_when_map_lookup_fails(self):
        polokwane = build_business_viability({**BASE, "location": "Polokwane, Limpopo"}, {"status": "unavailable"})
        tzaneen = build_business_viability({**BASE, "location": "Tzaneen, Limpopo"}, {"status": "unavailable"})
        location_score = lambda result: next(item["score"] for item in result["categoryScores"] if item["key"] == "locationMarket")
        self.assertEqual(location_score(polokwane), 56)
        self.assertEqual(location_score(tzaneen), 51)

    def test_all_nine_provinces_have_repeatable_industry_profiles(self):
        cases = {
            "Eastern Cape": "health",
            "Free State": "professional",
            "Gauteng": "manufacturing",
            "KwaZulu-Natal": "restaurant",
            "Limpopo": "health",
            "Mpumalanga": "agriculture",
            "Northern Cape": "tourism",
            "North West": "agriculture",
            "Western Cape": "tourism",
        }
        for province, category in cases.items():
            with self.subTest(province=province):
                values = {**BASE, "businessTypeCategory": category, "location": f"Town, {province}, South Africa"}
                first = build_business_viability(values, {"status": "unavailable"})
                second = build_business_viability(values, {"status": "unavailable"})
                self.assertEqual(first["score"], second["score"])
                self.assertEqual(first["locationEvidence"]["provinceLabel"], province)
                self.assertEqual(first["locationEvidence"]["provinceProfileAdjustment"], 3)

    def test_zero_or_negative_monthly_profit_is_reported_as_high_risk(self):
        values = {**BASE, "monthlyRevenue": 20000, "monthlyExpenses": 20000}
        result = build_business_viability(values, {"status": "ok", "contextDataAvailable": True, "mappedFeatureCount": 8, "relevantAnchors": 4, "competitorCount": 2})
        self.assertEqual(result["prediction"], "High risk of not becoming profitable")
        self.assertLessEqual(result["score"], 49)

    def test_industry_guidance_varies_by_sector(self):
        agriculture = build_business_viability({**BASE, "businessTypeCategory": "agriculture"}, {})
        restaurant = build_business_viability({**BASE, "businessTypeCategory": "restaurant"}, {})
        self.assertIn("water", agriculture["sectorGuidance"]["focus"].lower())
        self.assertIn("food", restaurant["sectorGuidance"]["focus"].lower())


if __name__ == "__main__":
    unittest.main()
