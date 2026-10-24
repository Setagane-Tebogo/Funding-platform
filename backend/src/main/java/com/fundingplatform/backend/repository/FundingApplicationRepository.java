package com.fundingplatform.backend.repository;

import com.fundingplatform.backend.entity.FundingApplication;
import com.fundingplatform.backend.entity.User;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;

public interface FundingApplicationRepository extends JpaRepository<FundingApplication, Long> {
    List<FundingApplication> findByEntrepreneurOrderByCreatedAtDesc(User entrepreneur);
}
