
package com.fundingplatform.backend.controller;

import com.fundingplatform.backend.dto.BusinessProfileRequest;
import com.fundingplatform.backend.dto.BusinessProfileResponse;
import com.fundingplatform.backend.service.BusinessProfileService;

import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/entrepreneur/business-profile")
public class BusinessProfileController {

    private final BusinessProfileService profileService;

    public BusinessProfileController(
            BusinessProfileService profileService) {
        this.profileService = profileService;
    }

    @PostMapping
    public ResponseEntity<?> create(
            @RequestBody BusinessProfileRequest request,
            Authentication authentication) {
        try {
            BusinessProfileResponse response =
                    profileService.create(
                            authentication.getName(), request);

            return ResponseEntity.status(HttpStatus.CREATED)
                    .body(response);

        } catch (IllegalArgumentException
                 | IllegalStateException e) {
            return ResponseEntity.badRequest().body(e.getMessage());

        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(e.getMessage());
        }
    }

    @GetMapping
    public ResponseEntity<?> getMyProfile(
            Authentication authentication) {
        try {
            return ResponseEntity.ok(
                    profileService.getMyProfile(
                            authentication.getName()));

        } catch (IllegalArgumentException e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND)
                    .body(e.getMessage());

        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(e.getMessage());
        }
    }

    @PutMapping
    public ResponseEntity<?> update(
            @RequestBody BusinessProfileRequest request,
            Authentication authentication) {
        try {
            return ResponseEntity.ok(
                    profileService.update(
                            authentication.getName(), request));

        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(e.getMessage());

        } catch (SecurityException e) {
            return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(e.getMessage());
        }
    }
}
