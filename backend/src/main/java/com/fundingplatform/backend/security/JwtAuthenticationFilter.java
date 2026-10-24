
package com.fundingplatform.backend.security;

import com.fundingplatform.backend.service.JwtService;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;

import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.List;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    private final JwtService jwtService;

    public JwtAuthenticationFilter(JwtService jwtService) {
        this.jwtService = jwtService;
    }

    @Override
    protected void doFilterInternal(
            HttpServletRequest request,
            HttpServletResponse response,
            FilterChain filterChain)
            throws ServletException, IOException {

        String path = request.getRequestURI();
        String authorizationHeader =
                request.getHeader("Authorization");

        if (authorizationHeader == null
                || !authorizationHeader.startsWith("Bearer ")) {

            System.out.println(
                    "JWT DEBUG: No Bearer token for " + path
            );

            filterChain.doFilter(request, response);
            return;
        }

        String token = authorizationHeader.substring(7).trim();

        if (!jwtService.isTokenValid(token)) {

            System.out.println(
                    "JWT DEBUG: Token validation failed for " + path
            );

            filterChain.doFilter(request, response);
            return;
        }

        String email = jwtService.extractEmail(token);
        String role = jwtService.extractRole(token);

        if (email == null || role == null || role.isBlank()) {
            System.out.println(
                    "JWT DEBUG: Token missing email or role for " + path
            );

            filterChain.doFilter(request, response);
            return;
        }

        var authentication =
                new UsernamePasswordAuthenticationToken(
                        email,
                        null,
                        List.of(
                                new SimpleGrantedAuthority("ROLE_" + role)
                        )
                );

        SecurityContextHolder.getContext()
                .setAuthentication(authentication);

        System.out.println(
                "JWT DEBUG: Authentication established for "
                + path + " | role=" + role
        );

        filterChain.doFilter(request, response);
    }
}
