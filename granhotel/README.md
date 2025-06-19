# Gran Hotel Management System - Perú Edition (Lite)

This project is a comprehensive hotel management system tailored for the Peruvian market, focusing on essential modules for small to medium hotels.

## Project Status

Currently, the initial backend for the **Room Management** module is under development.

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

5.  **Accessing the API:**
    *   The backend API should now be accessible at `http://localhost:8000`.
    *   API documentation (Swagger UI) is available at `http://localhost:8000/docs`.
    *   ReDoc documentation is available at `http://localhost:8000/redoc`.

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

## Next Steps
*   Frontend setup and development.
*   Implementation of other core modules.

---
*This README will be updated as the project progresses.*
