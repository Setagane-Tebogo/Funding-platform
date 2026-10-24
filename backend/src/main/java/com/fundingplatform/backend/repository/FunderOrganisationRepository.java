package com.fundingplatform.backend.repository;

import com.fundingplatform.backend.entity.FunderOrganisation;
import com.fundingplatform.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface FunderOrganisationRepository
        extends JpaRepository<FunderOrganisation, Long> {

    Optional<FunderOrganisation> findByUser(User user);

    boolean existsByUser(User user);
}