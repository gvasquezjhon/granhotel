# Gran Hotel Management System - Perú Edition (Lite)

This project is a comprehensive hotel management system tailored for the Peruvian market, focusing on essential modules for small to medium hotels. It includes a Python/FastAPI backend and a React/TypeScript/Vite/Tailwind CSS frontend.

## Project Status
*   **Backend:** All core modules (Rooms, Guests, Reservations, Users/Auth, Products, Inventory, Housekeeping, POS, Billing/Folios, Reporting) are implemented with models, services, APIs, and tests.
*   **Frontend:** Initial project setup (Vite, React, TS, Tailwind), basic layout, routing, AuthContext, and a functional Login Page (with API integration for login/logout and user fetching) are implemented. Development of feature modules is the next phase.

## Prerequisites
*   Docker
*   Docker Compose
*   Node.js and npm (or yarn/pnpm) - **Required on your local machine for initial frontend dependency installation and optimal local development experience.**

## Project Setup & Running (Docker Compose)

This project uses Docker Compose to manage multi-container application services (backend, frontend, database).

**1. Clone the Repository:**
   ```bash
   git clone <repository-url> # Replace <repository-url> with the actual URL
   cd granhotel
   ```

**2. Backend Configuration:**
   *   Navigate to the `backend` directory:
       ```bash
       cd backend
       ```
   *   Create a `.env` file by copying the example:
       ```bash
       cp .env.example .env
       ```
   *   Review and **update the variables in `backend/.env`**, especially `SECRET_KEY`, `REFRESH_SECRET_KEY`, and PostgreSQL credentials if you deviate from defaults. All necessary variables are listed in `.env.example`.

**3. Frontend Configuration:**
   *   Navigate to the `frontend` directory:
       ```bash
       cd frontend
       ```
   *   Create a `.env` file for Vite:
       ```bash
       # Create .env with the following content:
       echo "VITE_API_BASE_URL=http://localhost:8000/api/v1" > .env
       ```
       *(You can also copy `frontend/.env.example` to `frontend/.env` if an example file is provided in future updates).*
   *   The `VITE_API_BASE_URL` should point to your backend API. The default `http://localhost:8000/api/v1` is suitable when running with the provided Docker Compose setup, as Nginx (if used for backend in production) or the backend dev server will be available at `localhost:8000` from the perspective of your browser accessing the frontend.
   *   **(Important for Local Development):** Before the first `docker-compose up`, it's highly recommended to install frontend dependencies locally on your host machine:
       ```bash
       npm install
       # or yarn install / pnpm install
       ```
       This populates your local `frontend/node_modules` directory. The `docker-compose.yml` for the frontend service mounts `./frontend:/app` and uses a named volume `frontend_node_modules:/app/node_modules`. The `command` in `docker-compose.yml` (`sh -c "npm install && npm run dev -- --host"`) will then run `npm install` inside the container; if the named volume is already populated and `package.json` hasn't changed, this step will be very fast. This ensures Vite HMR works correctly by having `node_modules` available.

**4. Build and Run with Docker Compose:**
   *   Navigate back to the project root directory (`granhotel`):
       ```bash
       cd ..
       ```
   *   Run Docker Compose:
       ```bash
       docker-compose up --build
       ```
   *   The `--build` flag ensures images are built (or rebuilt if Dockerfiles or contexts change).
   *   To run in detached mode (in the background): `docker-compose up -d --build`.

**5. Database Migrations (First Time Setup / After Model Changes):**
   *   Once the containers are running (especially the `db` and `backend` services), apply database migrations. Open a **new terminal window**:
   *   Navigate to the project root (`granhotel`).
   *   Execute the Alembic upgrade command inside the running `backend` container:
       ```bash
       docker-compose exec backend alembic upgrade head
       ```
       This applies all migrations for all modules.

**6. Accessing the Applications:**
   *   **Backend API:** Accessible at `http://localhost:8000`.
       *   API documentation (Swagger UI): `http://localhost:8000/docs`.
       *   ReDoc documentation: `http://localhost:8000/redoc`.
   *   **Frontend Application:** Accessible at `http://localhost:3000` (or the port configured in `frontend/vite.config.ts` and `docker-compose.yml`).

**7. Running Backend Tests:**
   *   From the `granhotel` root directory:
       ```bash
       docker-compose exec backend pytest
       ```

**8. Stopping the Application:**
   *   Press `Ctrl+C` in the terminal where `docker-compose up` is running (if not in detached mode).
   *   If running in detached mode, or to ensure all services are stopped:
       ```bash
       docker-compose down
       ```
   *   To stop and remove volumes (e.g., to reset the database and frontend `node_modules` volume):
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
*   **Features:** Room availability checks, basic price calculation, reservation lifecycle management, blacklisted guest checks, rich response objects.

### User Management & Authentication
*   **Models:** `User` (UUID PK, email, hashed_password, role, etc.), `UserRole` enum.
*   **Security:** bcrypt password hashing, JWT (access/refresh tokens) via `python-jose`.
*   **API Endpoints:** `/api/v1/auth/` (login, refresh), `/api/v1/users/` (CRUD, status, role changes - admin/manager protected).
*   **Features:** RBAC, secure password storage, token-based authentication.

### Product Management
*   **Models:** `ProductCategory`, `Product` (price as Numeric, SKU, taxable status, etc.).
*   **API Endpoints:** `/api/v1/product-categories/` (CRUD), `/api/v1/products/` (CRUD, filters, price details with tax).
*   **Features:** Product catalog, IGV calculation, RBAC.

### Inventory Management
*   **Models:** `Supplier`, `InventoryItem`, `PurchaseOrder`, `PurchaseOrderItem`, `StockMovement`, related enums.
*   **API Endpoints:** `/api/v1/suppliers/` (CRUD), `/api/v1/inventory-stock/` (view/adjust stock, thresholds, history), `/api/v1/purchase-orders/` (CRUD, item receiving).
*   **Features:** Stock tracking, PO processing, stock audit trail, RBAC.

### Housekeeping Module
*   **Models:** `HousekeepingLog`, `HousekeepingTaskType`, `HousekeepingStatus`.
*   **API Endpoints:** `/api/v1/housekeeping/logs/` (CRUD, list by staff/room, status/assignment updates).
*   **Features:** Task scheduling, assignment, status tracking, RBAC.

### Point of Sale (POS) Module
*   **Models:** `POSSale`, `POSSaleItem`, `PaymentMethod`, `POSSaleStatus`.
*   **API Endpoints:** `/api/v1/pos/sales/` (create, list, get, void).
*   **Features:** Sales transactions, real-time inventory deduction, IGV calculation, various payment methods, RBAC.

### Billing & Guest Folio Management
*   **Models:** `GuestFolio`, `FolioTransaction`, `FolioStatus`, `FolioTransactionType`.
*   **API Endpoints:** `/api/v1/billing/folios/` (get/create for guest, add transactions, update status).
*   **Features:** Centralized guest charges/payments, balance calculation, folio lifecycle.

### Reporting & Analytics Module
*   **API Endpoints (under `/api/v1/reports/` - Manager/Admin access):**
    *   Occupancy (daily, period, RevPAR), Sales (summary, by category), Inventory (summary), Financials (folio summary).
*   **Features:** On-demand data aggregation for KPIs, structured Pydantic schemas for responses.

## Dependencies Added (Key Backend)
*   `passlib[bcrypt]`: For password hashing.
*   `python-jose[cryptography]`: For JWT creation, signing, and validation.

## Next Steps
*   **Frontend Development:** Build out UI components and pages for all backend modules. Implement forms, data display, and user interactions for Rooms, Guests, Reservations, POS, Inventory, Housekeeping, Billing, and User Management.
*   **Advanced Reporting:** Enhance the Reporting & Analytics module with more detailed reports, visualizations, and export options.
*   **Payment Gateway Integration:** For real-world payment processing in POS and Billing.
*   **Notifications System:** Implement email/SMS notifications for critical events (e.g., new reservations, low stock alerts, task assignments).
*   **Further Enhancements:** Based on specific hotel operational needs (e.g., group bookings, advanced pricing, detailed audit logs for more models, etc.).
*   **Deployment Configuration:** Finalize production Docker configurations, CI/CD pipelines.

---
*This README will be updated as the project progresses.*
