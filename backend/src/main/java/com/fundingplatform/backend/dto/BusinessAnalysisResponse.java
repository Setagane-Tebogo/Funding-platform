package com.fundingplatform.backend.dto;

import java.math.BigDecimal;

public record BusinessAnalysisResponse(
        String outlook,
        String summary,
        Integer estimatedBreakEvenMonths,
        BigDecimal estimatedMonthlyProfit,
        BigDecimal estimatedAnnualProfit,
        BigDecimal breakEvenRevenue,
        String confidence,
        String disclaimer) {
}
