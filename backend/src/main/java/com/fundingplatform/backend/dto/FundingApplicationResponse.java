package com.fundingplatform.backend.dto;

import com.fundingplatform.backend.entity.FundingApplication;
import java.time.LocalDateTime;

public record FundingApplicationResponse(Long id, Long programmeId, String programmeName, String proposal, String status, LocalDateTime createdAt) {
    public static FundingApplicationResponse from(FundingApplication application) {
        return new FundingApplicationResponse(application.getId(), application.getProgramme().getId(), application.getProgramme().getProgrammeName(), application.getProposal(), application.getStatus().name(), application.getCreatedAt());
    }
}
