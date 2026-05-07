# Authentication & Security Flow

This document describes the security architecture for the Job Wizard backend. GitHub natively renders the Mermaid diagram below.

## Overview
The system uses a standard **OAuth2 with Password Flow** using **JWT (JSON Web Tokens)** for session management and **Bcrypt** for password hashing.

## Authentication Flow

```mermaid
sequenceDiagram
    participant User as Frontend / User
    participant API as FastAPI (auth.py)
    participant Service as User Service
    participant Security as Security Core
    participant DB as PostgreSQL

    Note over User, DB: 1. Login Phase
    User->>API: POST /login (email, password)
    API->>Service: authenticate(email, password)
    Service->>DB: Fetch user by email
    DB-->>Service: User Record (Hashed Password)
    Service->>Security: verify_password(plain, hashed)
    Security-->>Service: Boolean Result
    
    alt is authenticated
        Service-->>API: User Object
        API->>Security: create_access_token(user_id)
        Security-->>API: JWT Token
        API-->>User: 200 OK {access_token, token_type: "bearer"}
    else invalid credentials
        API-->>User: 401 Unauthorized
    end

    Note over User, DB: 2. Protected Request Phase
    User->>API: GET /applications (Header: Authorization: Bearer <token>)
    API->>Security: jwt.decode(token)
    alt token is valid
        Security-->>API: Payload (sub: email)
        API->>DB: Fetch User
        DB-->>API: User Record
        API-->>User: 200 OK [Data]
    else token invalid/expired
        API-->>User: 401 Unauthorized
    end
```

## Security Implementation Details
1.  **Password Storage**: Never stored in plain text. We use `passlib` with the `bcrypt` algorithm.
2.  **Token Signing**: Tokens are signed using `HS256` with a `SECRET_KEY` defined in environment variables.
3.  **Token Expiration**: Access tokens are valid for 7 days by default.
4.  **Statelessness**: The backend does not store sessions in a database or Redis. All necessary user info is encoded in the JWT "subject" (email).
