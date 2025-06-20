# Gran Hotel Management System - Perú Edition (Lite)

This project is a comprehensive hotel management system tailored for the Peruvian market, focusing on essential modules for small to medium hotels.

## Project Status

Currently, the backend includes:
*   Room Management Module
*   Guest Management Module
*   Reservation System Module
*   User Management & JWT Authentication Module
*   Product Management Module
*   Inventory Management Module
*   Housekeeping Module
*   Point of Sale (POS) Module
*   Billing & Guest Folio Management Module
*   **Reporting & Analytics Module** (Occupancy, Sales, Inventory, Financial Summaries)
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
        *   `SECRET_KEY` (for JWT access tokens - IMPORTANT: Change for production)
        *   `REFRESH_SECRET_KEY` (for JWT refresh tokens - IMPORTANT: Change for production)
        *   `ALGORITHM` (e.g., HS256)
        *   `ACCESS_TOKEN_EXPIRE_MINUTES`
        *   `REFRESH_TOKEN_EXPIRE_DAYS`

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
    *   *This applies all migrations. No new tables were added for the reporting module itself as it reads existing data.*

5.  **Accessing the API:**
    *   The backend API should now be accessible at `http://localhost:8000`.
    *   API documentation (Swagger UI) is available at `http://localhost:8000/docs`.
    *   ReDoc documentation is available at `http://localhost:8000/redoc`.
    *   Available endpoint groups include:
        *   `/api/v1/auth/`
        *   `/api/v1/users/`
        *   `/api/v1/rooms/`
        *   `/api/v1/guests/`
        *   `/api/v1/reservations/`
        *   `/api/v1/product-categories/`
        *   `/api/v1/products/`
        *   `/api/v1/suppliers/`
        *   `/api/v1/inventory-stock/`
        *   `/api/v1/purchase-orders/`
        *   `/api/v1/housekeeping/`
        *   `/api/v1/billing/`
        *   `/api/v1/reports/` (New)

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

### Product Management
*   **Models:**
    *   `ProductCategory` (name, description).
    *   `Product` (name, description, price (Numeric), SKU, image URL, active/taxable status, relationship to `ProductCategory`).
*   **API Endpoints:**
    *   `/api/v1/product-categories/`: CRUD operations for product categories. (Creation/Update/Deletion typically Manager/Admin restricted).
    *   `/api/v1/products/`: CRUD operations for products. (Creation/Update/Deletion typically Manager/Admin restricted).
        *   Includes filtering by category, name, active status, taxable status.
        *   `GET /{product_id}/price-details`: Endpoint to get calculated price for a product quantity, including IGV (18%) if applicable.
*   **Features:** Management of a product catalog with categories. Precise price handling using `Numeric` type. Calculation of prices including Peruvian IGV. Role-based access control for managing products and categories.

### Inventory Management
*   **Core Functionality:** Enables tracking of product stock levels, management of suppliers, and processing of purchase orders.
*   **Models:**
    *   `Supplier`: Information about product vendors.
    *   `InventoryItem`: Tracks quantity on hand and low stock thresholds for each product.
    *   `PurchaseOrder` & `PurchaseOrderItem`: Manage orders to suppliers, including items, quantities, and status (Pending, Ordered, Received, etc.).
    *   `StockMovement`: Detailed audit trail of all changes to stock levels (e.g., initial stock, sales, purchase receipts, adjustments).
*   **API Endpoints:**
    *   `/api/v1/suppliers/`: Full CRUD operations for managing suppliers. (Creation/Update/Deletion typically Manager/Admin restricted).
    *   `/api/v1/inventory-stock/`:
        *   `GET /products/{product_id}`: View current stock details for a product.
        *   `POST /products/{product_id}/adjust-stock`: Manually adjust stock levels (Manager/Admin restricted).
        *   `PUT /products/{product_id}/low-stock-threshold`: Set low stock warning levels.
        *   `GET /low-stock`: List products at or below their low stock threshold.
        *   `GET /products/{product_id}/history`: View stock movement history for a product.
    *   `/api/v1/purchase-orders/`:
        *   `POST /`: Create new purchase orders with items.
        *   `GET /`: List purchase orders with filtering options.
        *   `GET /{po_id}`: Retrieve details of a specific purchase order.
        *   `PATCH /{po_id}/status`: Update the status of a purchase order (e.g., cancel).
        *   `POST /{po_id}/items/{po_item_id}/receive`: Record received items against a PO, which automatically updates product stock levels and PO status.
*   **Features:** Real-time stock tracking (via `InventoryItem` updates), audit trail for all stock changes (`StockMovement`), linkage between purchase order receipts and stock increases. Role-based access control for sensitive operations.

### Housekeeping Module
*   **Core Functionality:** Manages room cleaning schedules, assignments to housekeeping staff, and tracks the status of cleaning/maintenance tasks.
*   **Models:**
    *   `HousekeepingLog`: Records tasks with details like `room_id`, `assigned_to_user_id` (housekeeper), `task_type` (e.g., Full Clean, Turndown), `status` (e.g., Pending, In Progress, Completed), `scheduled_date`, `notes`, and audit timestamps/user IDs.
    *   Enums for `HousekeepingTaskType` and `HousekeepingStatus`.
*   **API Endpoints (under `/api/v1/housekeeping/`):**
    *   `/logs/`:
        *   `POST /`: Create new housekeeping tasks (Manager/Admin).
        *   `GET /`: List all tasks with filters (room, staff, status, date) (Manager/Admin).
    *   `/logs/staff/me`: View tasks assigned to the current logged-in housekeeper.
    *   `/logs/room/{room_id}`: View tasks for a specific room (Manager/Admin).
    *   `/logs/{log_id}`:
        *   `GET /`: Get details of a specific task. (Assigned staff or Manager/Admin).
        *   `PUT /`: Update task details (Manager/Admin).
        *   `PATCH /status`: Update task status (Assigned staff for allowed transitions, or Manager/Admin).
        *   `PATCH /assign`: Assign/reassign task to staff (Manager/Admin).
*   **Features:** Task assignment to specific housekeepers (User model with HOUSEKEEPER role). Tracking of task lifecycle via statuses. Audit trails for task creation and updates. Role-based access for managing and performing tasks.

### Billing & Guest Folio Management
*   **Core Functionality:** Consolidates all guest charges (room, POS, services) and payments onto a guest folio, providing a running balance and enabling final settlement.
*   **Models:**
    *   `GuestFolio`: Represents an individual guest's account, linked to a guest and optionally a reservation. Tracks `total_charges`, `total_payments`, and a calculated `balance`. Manages status (Open, Closed, Settled, Voided).
    *   `FolioTransaction`: Details each financial event on a folio (e.g., Room Charge, POS Charge, Payment, Refund, Discount). Linked to the folio and optionally to source records like POS sales or reservations.
    *   Enums for `FolioStatus` and `FolioTransactionType`.
*   **API Endpoints (under `/api/v1/billing/`):**
    *   `/folios/guest/{guest_id}`: List folios for a guest.
    *   `/folios/guest/{guest_id}/get-or-create`: Get an open folio for a guest (and optional reservation) or create a new one.
    *   `/folios/{folio_id}`: Get detailed folio information, including all transactions.
    *   `/folios/{folio_id}/transactions`: Add a new transaction (charge or payment) to a folio.
    *   `/folios/{folio_id}/status`: Update the status of a folio (e.g., to Close or Settle).
*   **Features:** Centralized guest billing. Automatic recalculation of folio balances after new transactions. Management of folio lifecycle (Open, Closed, Settled). Validation for key operations (e.g., folio must be open for new transactions, balance must be zero to settle). Role-based access for managing folios and transactions. (Future: Automatic posting of room charges, POS room charges to folio).

### Point of Sale (POS) Module
*   **Core Functionality:** Enables processing of sales transactions for products and services, calculating totals with applicable taxes, and updating inventory levels in real-time.
*   **Models:**
    *   `POSSale`: Records overall sale information including cashier, guest (optional), payment details (method, reference), calculated totals (before tax, tax, after tax), and status (Completed, Voided, etc.).
    *   `POSSaleItem`: Details each item sold within a sale, including product, quantity, and price/tax information at the time of sale for historical accuracy.
    *   Enums for `PaymentMethod` (Cash, Card, Yape, Plin, Room Charge, etc.) and `POSSaleStatus`.
*   **API Endpoints (under `/api/v1/pos/`):**
    *   `/sales/`:
        *   `POST /`: Create a new sales transaction. Accepts a list of items (product_id, quantity), payment method, and optional guest ID. Calculates totals, applies taxes (IGV 18%), and deducts sold items from inventory. (Accessible by Receptionist, Manager, Admin).
        *   `GET /`: List all sales transactions with filters (e.g., date range, cashier, guest, status). (Manager/Admin access).
        *   `GET /{sale_id}`: Retrieve details of a specific sale, including all items and related information. (Cashier for own sales, Manager/Admin for any).
        *   `POST /{sale_id}/void`: Void a completed sale. Records reason and voiding user. (Manager/Admin access).
*   **Features:** Real-time inventory deduction upon sale. Accurate price and tax (Peruvian IGV 18%) calculation at the item and sale level. Tracking of sales by cashier and optionally by guest. Support for various payment methods including Peruvian specifics. Role-based access for creating and managing sales.

### Reporting & Analytics Module
*   **Core Functionality:** Provides access to key operational and financial reports by aggregating data from various modules.
*   **API Endpoints (under `/api/v1/reports/` - Require Manager/Admin access):**
        *   `/occupancy/daily?target_date=YYYY-MM-DD`: Daily occupancy metrics.
        *   `/occupancy/period?date_from=...&date_to=...`: Occupancy metrics over a period.
        *   `/occupancy/revpar?date_from=...&date_to=...`: Revenue Per Available Room over a period.
        *   `/sales/summary-by-period?date_from=...&date_to=...[&payment_method=...]`: Summary of POS sales.
        *   `/sales/by-product-category?date_from=...&date_to=...`: POS sales grouped by product category.
        *   `/inventory/summary`: Current snapshot of inventory levels and values for active products.
        *   `/financials/folio-summary?date_from=...&date_to=...`: Summary of total charges and payments from guest folios.
*   **Features:** On-demand data aggregation for key performance indicators. Provides insights into occupancy, sales performance, inventory status, and basic financial summaries. Report data is structured using specific Pydantic schemas for clarity.
*   **Note:** More advanced inventory reports like "Low Stock Items" and "Stock Movement History" are available under the `/inventory-stock/` endpoints.

## Dependencies Added
*   `passlib[bcrypt]`: For password hashing.
*   `python-jose[cryptography]`: For JWT creation, signing, and validation.
    *(No new major dependencies for Reporting module itself, uses existing stack)*

## Next Steps
*   Frontend setup and development.
*   Implementation of a comprehensive Reporting & Analytics module (e.g. more advanced reports, dashboards, exports).
*   Enhanced validation, business logic, and features for existing modules:
    *   Room Management: Room features/amenities, advanced pricing rules.
    *   Reservation System: Group bookings, modification history, seasonal/promotional pricing.
    *   POS: Returns/refunds processing, direct linking of POS sales to guest folios for room charges.
    *   Inventory: Batch tracking, expiration dates for perishable goods, detailed inventory reports.
    *   Housekeeping: Automated task generation based on reservations, staff performance tracking.
    *   Billing: Invoice generation (PDF), integration with payment gateways, automated nightly audit processes.
*   Further refinement of user roles and permissions across all modules.
*   Notifications system (email, SMS) for guest and staff alerts.

---
*This README will be updated as the project progresses.*
