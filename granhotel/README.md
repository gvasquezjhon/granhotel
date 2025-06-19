# Gran Hotel Management System - Perú Edition (Lite)

This project is a comprehensive hotel management system tailored for the Peruvian market, focusing on essential modules for small to medium hotels.

## Project Status

Currently, the backend includes:
*   Room Management Module
*   Guest Management Module
*   Reservation System Module
*   **User Management & JWT Authentication Module**
*   Localization settings (es-PE, America/Lima)

## Prerequisites

*   Docker
*   Docker Compose

## Backend Setup (Local Development)

1.  **Clone the repository:**
    ```bash
    git clone <repository-url>
    cd granhotel
    ```

2.  **Configure Environment Variables:**
    *   Navigate to the `backend` directory:
        ```bash
        cd backend
        ```
    *   Create a `.env` file by copying the example:
        ```bash
        cp .env.example .env
        ```
        *(Note: If `.env.example` is not present in your version, you can manually create `.env` and populate it based on the structure of `.env.example` shown in documentation or previous setup steps. The `.env` file created in earlier steps can also be used directly if available).*
    *   Review and update the variables in `backend/.env` as needed. Key variables include:
        *   `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `DATABASE_URL`
        *   `DEFAULT_LANGUAGE`, `TIMEZONE`
        *   **`SECRET_KEY` (for JWT access tokens - IMPORTANT: Change for production)**
        *   **`REFRESH_SECRET_KEY` (for JWT refresh tokens - IMPORTANT: Change for production)**
        *   **`ALGORITHM` (e.g., HS256)**
        *   **`ACCESS_TOKEN_EXPIRE_MINUTES`**
        *   **`REFRESH_TOKEN_EXPIRE_DAYS`**

3.  **Build and Run with Docker Compose:**
    *   Navigate back to the project root directory (`granhotel`):
        ```bash
        cd ..
        ```
    *   Run Docker Compose:
        ```bash
        docker-compose up --build
        ```
    *   The `--build` flag ensures images are built (or rebuilt if changes are detected).
    *   To run in detached mode (in the background), use `docker-compose up -d --build`.

4.  **Database Migrations (First Time Setup / After Model Changes):**
    *   Once the containers are running (especially the `db` service), apply database migrations. Open a new terminal window:
    *   Navigate to the project root (`granhotel`).
    *   Execute the Alembic upgrade command inside the running `backend` container:
        ```bash
        docker-compose exec backend alembic upgrade head
        ```
    *   *This will apply all migrations, including those for rooms, guests, reservations, and users.*

5.  **Accessing the API:**
    *   The backend API should now be accessible at `http://localhost:8000`.
    *   API documentation (Swagger UI) is available at `http://localhost:8000/docs`.
    *   ReDoc documentation is available at `http://localhost:8000/redoc`.
    *   Available endpoint groups include:
        *   `/api/v1/auth/` (for login, token refresh)
        *   `/api/v1/users/` (for user management, protected)
        *   `/api/v1/rooms/`
        *   `/api/v1/guests/`
        *   `/api/v1/reservations/`

6.  **Running Tests:**
    *   To run the backend unit and integration tests, execute the following command from the `granhotel` root directory:
        ```bash
        docker-compose exec backend pytest
        ```
    *   This runs `pytest` inside the `backend` service container. The `pytest.ini` is configured with `pythonpath = .` which refers to the `WORKDIR /usr/src/app` inside the container, allowing `app.*` imports to work.

7.  **Stopping the Application:**
    *   To stop the services, press `Ctrl+C` in the terminal where `docker-compose up` is running.
    *   If running in detached mode, use:
        ```bash
        docker-compose down
        ```
    *   To stop and remove volumes (e.g., to reset the database):
        ```bash
        docker-compose down -v
        ```

## Implemented Modules (Backend)

### Room Management
*   **Models:** `Room` (with details like room_number, name, price, type, status, floor, building, timestamps).
*   **API Endpoints:** Full CRUD operations available under `/api/v1/rooms/`.
*   **Features:** Timezone-aware timestamps.

### Guest Management
*   **Models:** `Guest` (with details like name, document type (DNI, RUC, Passport, CE), document number, email, phone, address, nationality, preferences, blacklist status, timestamps).
*   **API Endpoints:** Full CRUD operations and blacklist toggle available under `/api/v1/guests/`.
*   **Features:** Peruvian document type enum, default country/nationality to Perú/Peruana, timezone-aware timestamps, basic validation for email and document numbers. Blacklist functionality. Filtering options on list retrieval.

### Reservation System
*   **Models:** `Reservation` (linking `Guest` and `Room`), `ReservationStatus` enum (Pending, Confirmed, Checked-In, Checked-Out, Cancelled, No-Show, Waitlist). Includes dates, calculated total price, notes, and timezone-aware timestamps.
*   **API Endpoints:** Full CRUD-like operations available under `/api/v1/reservations/`.
    *   `POST /`: Create a new reservation.
    *   `GET /`: List reservations with filters (guest, room, status, date range).
    *   `GET /{id}`: Retrieve a specific reservation.
    *   `PUT /{id}`: Update reservation details (dates, room, notes; re-checks availability and price).
    *   `PATCH /{id}/status`: Update reservation status.
    *   `POST /{id}/cancel`: Cancel a reservation.
*   **Features:** Room availability checks, basic price calculation (room rate * nights), management of reservation lifecycle through statuses. Blacklisted guests cannot make reservations. Rich reservation objects in responses including guest and room details.

### User Management & Authentication
*   **Models:** `User` (UUID PK, email, hashed_password, first_name, last_name, role, is_active), `UserRole` enum (Admin, Manager, Receptionist, Housekeeper).
*   **Security:** Passwords hashed using bcrypt. JWT (JSON Web Tokens) for API authentication using `python-jose`. Access and Refresh token strategy.
*   **API Endpoints:**
    *   `/api/v1/auth/login`: Authenticate user (email/password) and receive access/refresh tokens.
    *   `/api/v1/auth/refresh`: Obtain a new access token using a refresh token.
    *   `/api/v1/users/`: Endpoints for user management (CRUD-like operations).
        *   `POST /`: Create new users (Admin access).
        *   `GET /me`: Get current authenticated user's details.
        *   `PUT /me`: Update current user's details.
        *   `GET /`: List all users (Admin access).
        *   `GET /{user_id}`: Get user by ID (Admin or Manager access).
        *   `PUT /{user_id}`: Update user by ID (Admin access).
        *   `PATCH /{user_id}/activate` & `deactivate`: Manage user active status (Admin access).
        *   `PATCH /{user_id}/role`: Manage user role (Admin access).
*   **Features:** Role-based access control (RBAC) implemented for user management endpoints. Secure password storage. Token-based authentication for accessing protected resources.

## Dependencies Added
*   `passlib[bcrypt]`: For password hashing.
*   `python-jose[cryptography]`: For JWT creation, signing, and validation.

## Next Steps
*   Frontend setup and development.
*   Implementation of other core modules (e.g., Billing).
*   Enhanced validation, business logic, and features for existing modules (e.g., detailed room availability calendar, advanced pricing rules, IGV calculation, notifications for reservations).
*   Further refinement of user roles and permissions.

---
*This README will be updated as the project progresses.*
