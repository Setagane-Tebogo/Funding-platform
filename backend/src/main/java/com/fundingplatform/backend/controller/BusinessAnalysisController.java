package com.fundingplatform.backend.controller;

import com.fundingplatform.backend.dto.BusinessAnalysisRequest;
import com.fundingplatform.backend.service.BusinessAnalysisService;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/entrepreneur/business-analysis")
public class BusinessAnalysisController {
    private final BusinessAnalysisService analysisService;

    public BusinessAnalysisController(BusinessAnalysisService analysisService) {
        this.analysisService = analysisService;
    }

    @PostMapping
    public ResponseEntity<?> analyse(@RequestBody BusinessAnalysisRequest request) {
        try {
            return ResponseEntity.ok(analysisService.analyse(request));
        } catch (IllegalArgumentException exception) {
            return ResponseEntity.badRequest().body(exception.getMessage());
        }
    }
}
