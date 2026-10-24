package com.fundingplatform.backend.controller;

import com.fundingplatform.backend.dto.FundingApplicationRequest;
import com.fundingplatform.backend.dto.FundingApplicationResponse;
import com.fundingplatform.backend.entity.FundingApplication;
import com.fundingplatform.backend.entity.FundingProgramme;
import com.fundingplatform.backend.entity.User;
import com.fundingplatform.backend.repository.FundingApplicationRepository;
import com.fundingplatform.backend.repository.FundingProgrammeRepository;
import com.fundingplatform.backend.repository.UserRepository;
import java.util.List;
import org.springframework.http.*;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/entrepreneur/applications")
public class FundingApplicationController {
    private final FundingApplicationRepository applications;
    private final FundingProgrammeRepository programmes;
    private final UserRepository users;
    public FundingApplicationController(FundingApplicationRepository applications, FundingProgrammeRepository programmes, UserRepository users) { this.applications = applications; this.programmes = programmes; this.users = users; }
    @GetMapping
    public List<FundingApplicationResponse> mine(org.springframework.security.core.Authentication authentication) {
        User user = users.findByEmail(authentication.getName()).orElseThrow();
        return applications.findByEntrepreneurOrderByCreatedAtDesc(user).stream().map(FundingApplicationResponse::from).toList();
    }
    @PostMapping
    public ResponseEntity<?> submit(@RequestBody FundingApplicationRequest request, org.springframework.security.core.Authentication authentication) {
        if (request == null || request.programmeId() == null || request.proposal() == null || request.proposal().isBlank()) return ResponseEntity.badRequest().body("Programme and proposal are required.");
        User user = users.findByEmail(authentication.getName()).orElseThrow();
        FundingProgramme programme = programmes.findById(request.programmeId()).orElse(null);
        if (programme == null || !programme.isActive()) return ResponseEntity.status(HttpStatus.NOT_FOUND).body("Active funding programme not found.");
        FundingApplication application = new FundingApplication(); application.setEntrepreneur(user); application.setProgramme(programme); application.setProposal(request.proposal().trim());
        return ResponseEntity.status(HttpStatus.CREATED).body(FundingApplicationResponse.from(applications.save(application)));
    }
}
