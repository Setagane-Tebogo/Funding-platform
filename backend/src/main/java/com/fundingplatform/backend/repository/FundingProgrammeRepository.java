package com.fundingplatform.backend.repository;

import com.fundingplatform.backend.entity.FunderOrganisation;
import com.fundingplatform.backend.entity.FundingProgramme;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;

public interface FundingProgrammeRepository
        extends JpaRepository<FundingProgramme, Long> {

    List<FundingProgramme> findByOrganisation(
            FunderOrganisation organisation
    );

    List<FundingProgramme> findByActiveTrue();

    List<FundingProgramme> findByIndustryIgnoreCaseAndActiveTrue(
            String industry
    );

    List<FundingProgramme> findByBusinessStageIgnoreCaseAndActiveTrue(
            String businessStage
    );
}