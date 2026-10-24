package com.fundingplatform.backend.entity;

import jakarta.persistence.*;
import java.time.LocalDateTime;

@Entity
@Table(name = "funding_applications")
public class FundingApplication {
    @Id @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    @ManyToOne(optional = false) @JoinColumn(name = "entrepreneur_id")
    private User entrepreneur;
    @ManyToOne(optional = false) @JoinColumn(name = "programme_id")
    private FundingProgramme programme;
    @Column(nullable = false, columnDefinition = "TEXT")
    private String proposal;
    @Enumerated(EnumType.STRING) @Column(nullable = false)
    private ApplicationStatus status;
    @Column(nullable = false) private LocalDateTime createdAt;
    public FundingApplication() {}
    @PrePersist protected void onCreate() { if (createdAt == null) createdAt = LocalDateTime.now(); if (status == null) status = ApplicationStatus.SUBMITTED; }
    public Long getId() { return id; }
    public User getEntrepreneur() { return entrepreneur; }
    public void setEntrepreneur(User entrepreneur) { this.entrepreneur = entrepreneur; }
    public FundingProgramme getProgramme() { return programme; }
    public void setProgramme(FundingProgramme programme) { this.programme = programme; }
    public String getProposal() { return proposal; }
    public void setProposal(String proposal) { this.proposal = proposal; }
    public ApplicationStatus getStatus() { return status; }
    public LocalDateTime getCreatedAt() { return createdAt; }
}
