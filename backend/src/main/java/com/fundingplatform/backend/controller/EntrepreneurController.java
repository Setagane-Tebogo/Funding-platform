package com.fundingplatform.backend.controller;

import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/entrepreneur")
public class EntrepreneurController {

    @GetMapping("/dashboard")
    @PreAuthorize("hasAuthority('ROLE_ENTREPRENEUR')")
    public String dashboard(Authentication authentication) {

        return "Welcome to the Entrepreneur Dashboard, "
                + authentication.getName();
    }
}