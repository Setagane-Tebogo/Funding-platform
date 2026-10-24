
package com.fundingplatform.backend.controller;

import com.fundingplatform.backend.dto.FunderOrganisationResponse;
import com.fundingplatform.backend.entity.FunderOrganisation;
import com.fundingplatform.backend.entity.Role;
import com.fundingplatform.backend.entity.User;
import com.fundingplatform.backend.repository.FunderOrganisationRepository;
import com.fundingplatform.backend.repository.UserRepository;

import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/funder/organisation")
public class FunderOrganisationController {

    private final FunderOrganisationRepository organisationRepository;
    private final UserRepository userRepository;

    public FunderOrganisationController(
            FunderOrganisationRepository organisationRepository,
            UserRepository userRepository) {

        this.organisationRepository = organisationRepository;
        this.userRepository = userRepository;
    }

    @PostMapping
    public ResponseEntity<?> createOrganisation(
            @RequestBody FunderOrganisation organisation,
            Authentication authentication) {

        User user = userRepository
                .findByEmail(authentication.getName())
                .orElse(null);

        if (user == null) {
            return ResponseEntity.status(404).body("User not found");
        }

        if (user.getRole() != Role.FUNDER) {
            return ResponseEntity.status(403)
                    .body("Only funders can create an organisation");
        }

        if (organisationRepository.existsByUser(user)) {
            return ResponseEntity.badRequest()
                    .body("Organisation profile already exists");
        }

        // Never accept the owner from the request body.
        organisation.setUser(user);

        FunderOrganisation saved =
                organisationRepository.save(organisation);

        return ResponseEntity.ok(
                FunderOrganisationResponse.from(saved)
        );
    }

    @GetMapping
    public ResponseEntity<?> getOrganisation(
            Authentication authentication) {

        User user = userRepository
                .findByEmail(authentication.getName())
                .orElse(null);

        if (user == null) {
            return ResponseEntity.status(404).body("User not found");
        }

        if (user.getRole() != Role.FUNDER) {
            return ResponseEntity.status(403)
                    .body("Only funders can access this resource");
        }

        FunderOrganisation organisation = organisationRepository
                .findByUser(user)
                .orElse(null);

        if (organisation == null) {
            return ResponseEntity.status(404)
                    .body("Organisation profile not found");
        }

        return ResponseEntity.ok(
                FunderOrganisationResponse.from(organisation)
        );
    }
}
