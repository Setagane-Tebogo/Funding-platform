
package com.fundingplatform.backend.service;

import com.fundingplatform.backend.dto.BusinessProfileRequest;
import com.fundingplatform.backend.dto.BusinessProfileResponse;
import com.fundingplatform.backend.entity.BusinessProfile;
import com.fundingplatform.backend.entity.User;
import com.fundingplatform.backend.repository.BusinessProfileRepository;
import com.fundingplatform.backend.repository.UserRepository;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.math.BigDecimal;

@Service
public class BusinessProfileService {

    private final BusinessProfileRepository profileRepository;
    private final UserRepository userRepository;

    public BusinessProfileService(
            BusinessProfileRepository profileRepository,
            UserRepository userRepository) {
        this.profileRepository = profileRepository;
        this.userRepository = userRepository;
    }

    @Transactional
    public BusinessProfileResponse create(
            String email,
            BusinessProfileRequest request) {

        User user = getEntrepreneur(email);

        if (profileRepository.existsByUser(user)) {
            throw new IllegalStateException(
                    "You already have a business profile. Update it instead.");
        }

        validate(request);

        BusinessProfile profile = new BusinessProfile();
        profile.setUser(user);
        applyRequest(profile, request);

        return BusinessProfileResponse.from(
                profileRepository.save(profile));
    }

    @Transactional(readOnly = true)
    public BusinessProfileResponse getMyProfile(String email) {
        User user = getEntrepreneur(email);

        BusinessProfile profile = profileRepository.findByUser(user)
                .orElseThrow(() -> new IllegalArgumentException(
                        "Business profile not found. Create one first."));

        return BusinessProfileResponse.from(profile);
    }

    @Transactional
    public BusinessProfileResponse update(
            String email,
            BusinessProfileRequest request) {

        User user = getEntrepreneur(email);

        BusinessProfile profile = profileRepository.findByUser(user)
                .orElseThrow(() -> new IllegalArgumentException(
                        "Business profile not found. Create one first."));

        validate(request);
        applyRequest(profile, request);

        return BusinessProfileResponse.from(
                profileRepository.save(profile));
    }

    private User getEntrepreneur(String email) {
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new IllegalArgumentException(
                        "Authenticated user not found."));

        if (user.getRole() != com.fundingplatform.backend.entity.Role.ENTREPRENEUR) {
            throw new SecurityException(
                    "Only entrepreneurs can manage business profiles.");
        }

        return user;
    }

    private void validate(BusinessProfileRequest request) {
        if (request == null
                || isBlank(request.businessName())
                || isBlank(request.industry())
                || isBlank(request.businessStage())
                || isBlank(request.description())
                || isBlank(request.location())) {
            throw new IllegalArgumentException(
                    "Business name, industry, stage, description and location are required.");
        }

        if (request.fundingNeeded() != null
                && request.fundingNeeded().compareTo(BigDecimal.ZERO) < 0) {
            throw new IllegalArgumentException(
                    "Funding needed cannot be negative.");
        }
    }

    private boolean isBlank(String value) {
        return value == null || value.isBlank();
    }

    private void applyRequest(
            BusinessProfile profile,
            BusinessProfileRequest request) {

        profile.setBusinessName(request.businessName().trim());
        profile.setIndustry(request.industry().trim());
        profile.setBusinessStage(request.businessStage().trim());
        profile.setDescription(request.description().trim());
        profile.setLocation(request.location().trim());
        profile.setFundingNeeded(request.fundingNeeded());
        profile.setIntendedUseOfFunds(request.intendedUseOfFunds());
    }
}
