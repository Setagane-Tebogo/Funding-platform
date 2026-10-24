package com.fundingplatform.backend.controller;

import org.springframework.security.core.Authentication;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/funder")
public class FunderController {

    @GetMapping("/dashboard")
    public String dashboard(Authentication authentication) {

        return "Welcome to the Funder Dashboard, "
                + authentication.getName();
    }
}