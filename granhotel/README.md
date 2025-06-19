# Gran Hotel Management System - Perú Edition (Lite)

This project is a comprehensive hotel management system tailored for the Peruvian market, focusing on essential modules for small to medium hotels.

## Project Status

Currently, the backend includes:
*   **Room Management Module:** CRUD operations, status tracking, etc.
*   **Guest Management Module:** CRUD operations, Peruvian document types, blacklisting functionality.
*   Localization settings for es-PE and America/Lima timezone.

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
        *   `POSTGRES_USER`
        *   `POSTGRES_PASSWORD`
        *   `POSTGRES_DB`
        *   `DATABASE_URL` (this is typically constructed from the above, ensure it points to the `db` service name, e.g., `postgresql://user:pass@db:5432/dbname`)
        *   `CORS_ORIGINS`
        *   `DEFAULT_LANGUAGE`
        *   `TIMEZONE`

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
    *   *This will apply all migrations, including those for rooms and guests.*

5.  **Accessing the API:**
    *   The backend API should now be accessible at `http://localhost:8000`.
    *   API documentation (Swagger UI) is available at `http://localhost:8000/docs`.
    *   ReDoc documentation is available at `http://localhost:8000/redoc`.
    *   Available endpoint groups include:
        *   `/api/v1/rooms/`
        *   `/api/v1/guests/`

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

## Next Steps
*   Frontend setup and development.
*   Implementation of other core modules (e.g., Reservations, Billing).
*   Enhanced validation and business logic for existing modules.
*   User authentication and authorization.

---
*This README will be updated as the project progresses.*
