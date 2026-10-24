
package com.fundingplatform.backend.dto;

import com.fundingplatform.backend.entity.FundingProgramme;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

public record FundingProgrammeResponse(
        Long id,
        String programmeName,
        String fundingType,
        BigDecimal minimumFunding,
        BigDecimal maximumFunding,
        String industry,
        String businessStage,
        String location,
        String description,
        String requirements,
        LocalDate applicationDeadline,
        boolean active,
        LocalDateTime createdAt,
        Long organisationId,
        String organisationName
) {
    public static FundingProgrammeResponse from(
            FundingProgramme programme) {

        return new FundingProgrammeResponse(
                programme.getId(),
                programme.getProgrammeName(),
                programme.getFundingType(),
                programme.getMinimumFunding(),
                programme.getMaximumFunding(),
                programme.getIndustry(),
                programme.getBusinessStage(),
                programme.getLocation(),
                programme.getDescription(),
                programme.getRequirements(),
                programme.getApplicationDeadline(),
                programme.isActive(),
                programme.getCreatedAt(),
                programme.getOrganisation().getId(),
                programme.getOrganisation().getOrganisationName()
        );
    }
}
