
package com.fundingplatform.backend.controller;

import com.fundingplatform.backend.dto.LoginRequest;
import com.fundingplatform.backend.dto.LoginResponse;
import com.fundingplatform.backend.dto.UserResponse;
import com.fundingplatform.backend.entity.Role;
import com.fundingplatform.backend.entity.User;
import com.fundingplatform.backend.repository.UserRepository;
import com.fundingplatform.backend.service.JwtService;

import org.springframework.http.ResponseEntity;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/auth")
public class AuthController {

    private final UserRepository userRepository;
    private final PasswordEncoder passwordEncoder;
    private final JwtService jwtService;

    public AuthController(
            UserRepository userRepository,
            PasswordEncoder passwordEncoder,
            JwtService jwtService) {

        this.userRepository = userRepository;
        this.passwordEncoder = passwordEncoder;
        this.jwtService = jwtService;
    }

    // REGISTER
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody User user) {

        if (user.getName() == null || user.getName().isBlank()
                || user.getEmail() == null || user.getEmail().isBlank()
                || user.getPassword() == null || user.getPassword().isBlank()) {

            return ResponseEntity.badRequest()
                    .body("Name, email and password are required");
        }

        if (userRepository.existsByEmail(user.getEmail())) {
            return ResponseEntity.badRequest()
                    .body("Email already registered");
        }

        // Public registration is for entrepreneurs. Funder and admin accounts
        // must be provisioned through an approved process.
        user.setRole(Role.ENTREPRENEUR);

        user.setPassword(
                passwordEncoder.encode(user.getPassword())
        );

        User savedUser = userRepository.save(user);

        return ResponseEntity.ok(
                UserResponse.from(savedUser)
        );
    }

    // LOGIN
    @PostMapping("/login")
    public ResponseEntity<?> login(
            @RequestBody LoginRequest request) {

        if (request.getEmail() == null
                || request.getEmail().isBlank()
                || request.getPassword() == null
                || request.getPassword().isBlank()) {

            return ResponseEntity.badRequest()
                    .body("Email and password are required");
        }

        User user = userRepository
                .findByEmail(request.getEmail())
                .orElse(null);

        if (user == null) {
            return ResponseEntity.status(401)
                    .body("Invalid email or password");
        }

        boolean passwordMatches = passwordEncoder.matches(
                request.getPassword(),
                user.getPassword()
        );

        if (!passwordMatches) {
            return ResponseEntity.status(401)
                    .body("Invalid email or password");
        }

        String token = jwtService.generateToken(
                user.getEmail(),
                user.getRole().name()
        );

        LoginResponse response = new LoginResponse(
                token,
                user.getId(),
                user.getName(),
                user.getEmail(),
                user.getRole().name()
        );

        return ResponseEntity.ok(response);
    }
}
