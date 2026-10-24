
package com.fundingplatform.backend.dto;

import com.fundingplatform.backend.entity.BusinessProfile;
import java.math.BigDecimal;
import java.time.LocalDateTime;

public record BusinessProfileResponse(
        Long id,
        String businessName,
        String industry,
        String businessStage,
        String description,
        String location,
        BigDecimal fundingNeeded,
        String intendedUseOfFunds,
        LocalDateTime createdAt,
        LocalDateTime updatedAt
) {
    public static BusinessProfileResponse from(
            BusinessProfile profile) {

        return new BusinessProfileResponse(
                profile.getId(),
                profile.getBusinessName(),
                profile.getIndustry(),
                profile.getBusinessStage(),
                profile.getDescription(),
                profile.getLocation(),
                profile.getFundingNeeded(),
                profile.getIntendedUseOfFunds(),
                profile.getCreatedAt(),
                profile.getUpdatedAt()
        );
    }
}
