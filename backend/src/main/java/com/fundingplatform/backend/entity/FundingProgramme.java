package com.fundingplatform.backend.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDate;
import java.time.LocalDateTime;

@Entity
@Table(name = "funding_programmes")
public class FundingProgramme {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne
    @JoinColumn(name = "organisation_id", nullable = false)
    private FunderOrganisation organisation;

    @Column(nullable = false)
    private String programmeName;

    @Column(nullable = false)
    private String fundingType;

    @Column(nullable = false, precision = 15, scale = 2)
    private BigDecimal minimumFunding;

    @Column(nullable = false, precision = 15, scale = 2)
    private BigDecimal maximumFunding;

    @Column(nullable = false)
    private String industry;

    @Column(nullable = false)
    private String businessStage;

    @Column(nullable = false)
    private String location;

    @Column(columnDefinition = "TEXT")
    private String description;

    @Column(columnDefinition = "TEXT")
    private String requirements;

    private LocalDate applicationDeadline;

    @Column(nullable = false)
    private boolean active;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    public FundingProgramme() {
    }

    @PrePersist
    protected void onCreate() {
        if (createdAt == null) createdAt = LocalDateTime.now();
    }

    public FundingProgramme(
            FunderOrganisation organisation,
            String programmeName,
            String fundingType,
            BigDecimal minimumFunding,
            BigDecimal maximumFunding,
            String industry,
            String businessStage,
            String location,
            String description,
            String requirements,
            LocalDate applicationDeadline) {

        this.organisation = organisation;
        this.programmeName = programmeName;
        this.fundingType = fundingType;
        this.minimumFunding = minimumFunding;
        this.maximumFunding = maximumFunding;
        this.industry = industry;
        this.businessStage = businessStage;
        this.location = location;
        this.description = description;
        this.requirements = requirements;
        this.applicationDeadline = applicationDeadline;
        this.active = true;
        this.createdAt = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public FunderOrganisation getOrganisation() {
        return organisation;
    }

    public void setOrganisation(FunderOrganisation organisation) {
        this.organisation = organisation;
    }

    public String getProgrammeName() {
        return programmeName;
    }

    public void setProgrammeName(String programmeName) {
        this.programmeName = programmeName;
    }

    public String getFundingType() {
        return fundingType;
    }

    public void setFundingType(String fundingType) {
        this.fundingType = fundingType;
    }

    public BigDecimal getMinimumFunding() {
        return minimumFunding;
    }

    public void setMinimumFunding(BigDecimal minimumFunding) {
        this.minimumFunding = minimumFunding;
    }

    public BigDecimal getMaximumFunding() {
        return maximumFunding;
    }

    public void setMaximumFunding(BigDecimal maximumFunding) {
        this.maximumFunding = maximumFunding;
    }

    public String getIndustry() {
        return industry;
    }

    public void setIndustry(String industry) {
        this.industry = industry;
    }

    public String getBusinessStage() {
        return businessStage;
    }

    public void setBusinessStage(String businessStage) {
        this.businessStage = businessStage;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getRequirements() {
        return requirements;
    }

    public void setRequirements(String requirements) {
        this.requirements = requirements;
    }

    public LocalDate getApplicationDeadline() {
        return applicationDeadline;
    }

    public void setApplicationDeadline(LocalDate applicationDeadline) {
        this.applicationDeadline = applicationDeadline;
    }

    public boolean isActive() {
        return active;
    }

    public void setActive(boolean active) {
        this.active = active;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }
}
