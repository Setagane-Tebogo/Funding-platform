
package com.fundingplatform.backend.controller;

import com.fundingplatform.backend.dto.FundingProgrammeResponse;
import com.fundingplatform.backend.entity.FunderOrganisation;
import com.fundingplatform.backend.entity.FundingProgramme;
import com.fundingplatform.backend.entity.Role;
import com.fundingplatform.backend.entity.User;
import com.fundingplatform.backend.repository.FunderOrganisationRepository;
import com.fundingplatform.backend.repository.FundingProgrammeRepository;
import com.fundingplatform.backend.repository.UserRepository;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/funder/programmes")
public class FundingProgrammeController {

    private final FundingProgrammeRepository programmeRepository;
    private final FunderOrganisationRepository organisationRepository;
    private final UserRepository userRepository;

    public FundingProgrammeController(
            FundingProgrammeRepository programmeRepository,
            FunderOrganisationRepository organisationRepository,
            UserRepository userRepository) {

        this.programmeRepository = programmeRepository;
        this.organisationRepository = organisationRepository;
        this.userRepository = userRepository;
    }

    @PostMapping
    public ResponseEntity<?> createProgramme(
            @RequestBody FundingProgramme programme,
            Authentication authentication) {

        User user = userRepository
                .findByEmail(authentication.getName())
                .orElse(null);

        if (user == null) {
            return ResponseEntity.status(404).body("User not found");
        }

        if (user.getRole() != Role.FUNDER) {
            return ResponseEntity.status(403)
                    .body("Only funders can create funding programmes");
        }

        FunderOrganisation organisation = organisationRepository
                .findByUser(user)
                .orElse(null);

        if (organisation == null) {
            return ResponseEntity.status(404)
                    .body("Please create an organisation profile first");
        }

        programme.setOrganisation(organisation);
        programme.setActive(true);

        FundingProgramme saved =
                programmeRepository.save(programme);

        return ResponseEntity.ok(
                FundingProgrammeResponse.from(saved)
        );
    }

    @GetMapping
    public ResponseEntity<?> getMyProgrammes(
            Authentication authentication) {

        User user = userRepository
                .findByEmail(authentication.getName())
                .orElse(null);

        if (user == null) {
            return ResponseEntity.status(404).body("User not found");
        }

        FunderOrganisation organisation = organisationRepository
                .findByUser(user)
                .orElse(null);

        if (organisation == null) {
            return ResponseEntity.status(404)
                    .body("Organisation profile not found");
        }

        List<FundingProgrammeResponse> programmes =
                programmeRepository.findByOrganisation(organisation)
                        .stream()
                        .map(FundingProgrammeResponse::from)
                        .toList();

        return ResponseEntity.ok(programmes);
    }

    @GetMapping("/active")
    public ResponseEntity<List<FundingProgrammeResponse>>
            getActiveProgrammes() {

        return ResponseEntity.ok(
                programmeRepository.findByActiveTrue()
                        .stream()
                        .map(FundingProgrammeResponse::from)
                        .toList()
        );
    }

    @GetMapping("/industry/{industry}")
    public ResponseEntity<List<FundingProgrammeResponse>>
            getByIndustry(@PathVariable String industry) {

        return ResponseEntity.ok(
                programmeRepository
                        .findByIndustryIgnoreCaseAndActiveTrue(industry)
                        .stream()
                        .map(FundingProgrammeResponse::from)
                        .toList()
        );
    }

    @GetMapping("/stage/{businessStage}")
    public ResponseEntity<List<FundingProgrammeResponse>>
            getByBusinessStage(@PathVariable String businessStage) {

        return ResponseEntity.ok(
                programmeRepository
                        .findByBusinessStageIgnoreCaseAndActiveTrue(
                                businessStage)
                        .stream()
                        .map(FundingProgrammeResponse::from)
                        .toList()
        );
    }
}
