
package com.fundingplatform.backend.dto;

import com.fundingplatform.backend.entity.FunderOrganisation;
import java.time.LocalDateTime;

public record FunderOrganisationResponse(
        Long id,
        String organisationName,
        String organisationType,
        String description,
        String website,
        String phone,
        String location,
        LocalDateTime createdAt
) {
    public static FunderOrganisationResponse from(
            FunderOrganisation organisation) {

        return new FunderOrganisationResponse(
                organisation.getId(),
                organisation.getOrganisationName(),
                organisation.getOrganisationType(),
                organisation.getDescription(),
                organisation.getWebsite(),
                organisation.getPhone(),
                organisation.getLocation(),
                organisation.getCreatedAt()
        );
    }
}
