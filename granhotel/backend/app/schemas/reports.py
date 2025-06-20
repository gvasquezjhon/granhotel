from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import date, datetime # Added datetime
from decimal import Decimal
from app.models.pos import PaymentMethod # For payment_method_filter if using enum

# --- Occupancy Report Schemas ---
class DailyOccupancyData(BaseModel):
    date: date
    total_rooms: int
    occupied_rooms: int
    occupancy_rate: float = Field(..., ge=0, le=100)
    error: Optional[str] = None

    class Config:
        from_attributes = True

class PeriodOccupancyData(BaseModel):
    date_from: date
    date_to: date
    number_of_days: int
    total_physical_rooms: int
    total_room_nights_available: int
    total_room_nights_occupied: int
    average_occupancy_rate: float = Field(..., ge=0, le=100)
    error: Optional[str] = None

    class Config:
        from_attributes = True

class RevPARData(BaseModel):
    date_from: date
    date_to: date
    total_room_revenue: str # Service returns stringified Decimal
    total_available_room_nights: int
    revpar: str # Service returns stringified Decimal
    error: Optional[str] = None

    class Config:
        from_attributes = True


# --- Sales Report Schemas ---
class TotalSalesSummary(BaseModel):
    date_from: date
    date_to: date
    payment_method_filter: Optional[PaymentMethod] = None # Using the enum now
    total_sales_after_tax: str # Service returns stringified Decimal
    total_sales_before_tax: str # Service returns stringified Decimal
    total_tax_amount: str # Service returns stringified Decimal
    number_of_sales: int

    class Config:
        from_attributes = True


class SalesByCategoryItem(BaseModel):
    category_name: str
    total_sales: str # Service returns stringified Decimal

    class Config:
        from_attributes = True

class SalesByProductCategoryReport(BaseModel):
    date_from: date
    date_to: date
    data: List[SalesByCategoryItem]

    class Config:
        from_attributes = True


# --- Inventory Report Schemas ---
class InventorySummaryItem(BaseModel):
    product_id: int
    product_name: str
    quantity_on_hand: int
    unit_value: str # Service returns stringified Decimal
    total_stock_value: str # Service returns stringified Decimal

    class Config:
        from_attributes = True

class InventorySummaryReport(BaseModel):
    generated_at: datetime
    data: List[InventorySummaryItem]

    class Config:
        from_attributes = True


# --- Financial Report Schemas (Folios) ---
class FolioFinancialSummary(BaseModel):
    date_from: date
    date_to: date
    total_charges_posted: str # Service returns stringified Decimal
    total_payments_received: str # Service returns stringified Decimal

    class Config:
        from_attributes = True

# --- General Purpose / More Complex Report Item Schemas (Examples if needed later) ---
class ReportMetricItem(BaseModel):
    label: str
    value: Any
    unit: Optional[str] = None

class ComplexReportSection(BaseModel):
    section_title: str
    metrics: List[ReportMetricItem]
    # sub_sections: Optional[List['ComplexReportSection']] # For nested reports

# If using Pydantic v1 and forward refs:
# ComplexReportSection.update_forward_refs()
# For Pydantic v2, forward refs are handled differently (usually string type hints or postponed annotations)
# but not needed for these current schemas.
