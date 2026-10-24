
package com.fundingplatform.backend.repository;

import com.fundingplatform.backend.entity.BusinessProfile;
import com.fundingplatform.backend.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.Optional;

public interface BusinessProfileRepository
        extends JpaRepository<BusinessProfile, Long> {

    Optional<BusinessProfile> findByUser(User user);

    boolean existsByUser(User user);
}
