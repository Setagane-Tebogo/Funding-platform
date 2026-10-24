package com.fundingplatform.backend.service;

import com.fundingplatform.backend.dto.BusinessAnalysisRequest;
import com.fundingplatform.backend.dto.BusinessAnalysisResponse;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;

@Service
public class BusinessAnalysisService {
    public BusinessAnalysisResponse analyse(BusinessAnalysisRequest request) {
        if (request == null || request.startupCosts() == null
                || request.monthlyRevenue() == null || request.monthlyExpenses() == null) {
            throw new IllegalArgumentException("Startup costs, monthly revenue and monthly expenses are required.");
        }
        if (request.startupCosts().signum() < 0 || request.monthlyRevenue().signum() < 0
                || request.monthlyExpenses().signum() < 0) {
            throw new IllegalArgumentException("Financial values cannot be negative.");
        }

        BigDecimal monthlyProfit = request.monthlyRevenue().subtract(request.monthlyExpenses());
        BigDecimal annualProfit = monthlyProfit.multiply(BigDecimal.valueOf(12)).setScale(2, RoundingMode.HALF_UP);
        String outlook;
        Integer breakEvenMonths = null;
        String summary;
        if (monthlyProfit.signum() > 0) {
            breakEvenMonths = request.startupCosts().divide(monthlyProfit, 0, RoundingMode.CEILING).intValue();
            outlook = "Potentially profitable";
            summary = "Your projected revenue is higher than your projected monthly expenses.";
        } else if (monthlyProfit.signum() == 0) {
            outlook = "Break-even only";
            summary = "Your current projection covers operating costs but does not recover startup costs.";
        } else {
            outlook = "Needs improvement";
            summary = "Your projected monthly expenses are higher than your projected revenue.";
        }

        return new BusinessAnalysisResponse(
                outlook, summary, breakEvenMonths, monthlyProfit.setScale(2, RoundingMode.HALF_UP),
                annualProfit, request.monthlyExpenses().setScale(2, RoundingMode.HALF_UP),
                monthlyProfit.signum() > 0 ? "Medium" : "Low",
                "This is an advisory estimate based only on the figures you entered. It is not a funding or profit guarantee.");
    }
}
