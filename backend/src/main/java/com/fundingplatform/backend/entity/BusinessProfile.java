
package com.fundingplatform.backend.entity;

import jakarta.persistence.*;
import java.math.BigDecimal;
import java.time.LocalDateTime;

@Entity
@Table(
    name = "business_profiles",
    uniqueConstraints = {
        @UniqueConstraint(
            name = "uk_business_profile_user",
            columnNames = "user_id"
        )
    }
)
public class BusinessProfile {

    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @OneToOne(fetch = FetchType.LAZY, optional = false)
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false)
    private String businessName;

    @Column(nullable = false)
    private String industry;

    @Column(nullable = false)
    private String businessStage;

    @Column(nullable = false, length = 2000)
    private String description;

    @Column(nullable = false)
    private String location;

    @Column(precision = 14, scale = 2)
    private BigDecimal fundingNeeded;

    @Column(length = 1000)
    private String intendedUseOfFunds;

    @Column(nullable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    public BusinessProfile() {
    }

    @PrePersist
    protected void onCreate() {
        LocalDateTime now = LocalDateTime.now();
        createdAt = now;
        updatedAt = now;
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }

    public Long getId() {
        return id;
    }

    public User getUser() {
        return user;
    }

    public void setUser(User user) {
        this.user = user;
    }

    public String getBusinessName() {
        return businessName;
    }

    public void setBusinessName(String businessName) {
        this.businessName = businessName;
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

    public String getDescription() {
        return description;
    }

    public void setDescription(String description) {
        this.description = description;
    }

    public String getLocation() {
        return location;
    }

    public void setLocation(String location) {
        this.location = location;
    }

    public BigDecimal getFundingNeeded() {
        return fundingNeeded;
    }

    public void setFundingNeeded(BigDecimal fundingNeeded) {
        this.fundingNeeded = fundingNeeded;
    }

    public String getIntendedUseOfFunds() {
        return intendedUseOfFunds;
    }

    public void setIntendedUseOfFunds(String intendedUseOfFunds) {
        this.intendedUseOfFunds = intendedUseOfFunds;
    }

    public LocalDateTime getCreatedAt() {
        return createdAt;
    }

    public LocalDateTime getUpdatedAt() {
        return updatedAt;
    }
}
