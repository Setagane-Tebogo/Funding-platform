package com.fundingplatform.backend.dto;

import java.math.BigDecimal;

public record BusinessAnalysisRequest(
        BigDecimal startupCosts,
        BigDecimal monthlyRevenue,
        BigDecimal monthlyExpenses,
        BigDecimal monthlyGrowthPercent) {
}
