package com.fundingplatform.backend.dto;

import java.math.BigDecimal;

public record BusinessProfileRequest(
        String businessName,
        String industry,
        String businessStage,
        String description,
        String location,
        BigDecimal fundingNeeded,
        String intendedUseOfFunds
) {
}
