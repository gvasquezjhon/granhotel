from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Any, Optional, Dict
from datetime import date

from app import schemas # Now includes schemas.reports
from app.models import User as UserModel # Explicitly import User model for current_user
from app import services
from app.api import deps
from app.db import session as db_session
from app.models.pos import PaymentMethod # For query param enum

router = APIRouter()

@router.get("/occupancy/daily", response_model=Dict[str, Any])
def get_daily_occupancy_report_api(
    *,
    db: Session = Depends(db_session.get_db),
    target_date: date = Query(..., description="Target date for the report (YYYY-MM-DD)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Get daily occupancy report for a specific date.'''
    try:
        report_data = services.reporting_service.get_daily_occupancy_data(db, target_date=target_date)
        return report_data
    except ValueError as e: # Catch potential ValueErrors from service (e.g., date_from > date_to)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e: # Catch any other unexpected errors
        # Log error e here
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the report.")


@router.get("/occupancy/period", response_model=Dict[str, Any])
def get_period_occupancy_report_api(
    *,
    db: Session = Depends(db_session.get_db),
    date_from: date = Query(..., description="Start date for the report period (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date for the report period (YYYY-MM-DD)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Get occupancy rate report over a specified period.'''
    try:
        report_data = services.reporting_service.get_occupancy_rate_over_period(db, date_from=date_from, date_to=date_to)
        return report_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the report.")


@router.get("/occupancy/revpar", response_model=Dict[str, Any])
def get_revpar_report_api(
    *,
    db: Session = Depends(db_session.get_db),
    date_from: date = Query(..., description="Start date for RevPAR calculation (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date for RevPAR calculation (YYYY-MM-DD)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Get Revenue Per Available Room (RevPAR) report over a period.'''
    try:
        report_data = services.reporting_service.get_revpar_over_period(db, date_from=date_from, date_to=date_to)
        return report_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the report.")


@router.get("/sales/summary-by-period", response_model=Dict[str, Any])
def get_total_sales_report_api(
    *,
    db: Session = Depends(db_session.get_db),
    date_from: date = Query(..., description="Start date for sales summary (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date for sales summary (YYYY-MM-DD)"),
    payment_method: Optional[PaymentMethod] = Query(None, description="Filter by payment method"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Get summary of total POS sales over a period, optionally filtered by payment method.'''
    try:
        report_data = services.reporting_service.get_total_sales_by_period(db, date_from=date_from, date_to=date_to, payment_method=payment_method)
        return report_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the report.")

@router.get("/sales/by-product-category", response_model=List[Dict[str, Any]])
def get_sales_by_category_report_api(
    *,
    db: Session = Depends(db_session.get_db),
    date_from: date = Query(..., description="Start date for category sales (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date for category sales (YYYY-MM-DD)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Get breakdown of POS sales by product category over a period.'''
    try:
        report_data = services.reporting_service.get_sales_by_product_category(db, date_from=date_from, date_to=date_to)
        return report_data
    except ValueError as e: # Catch date_from > date_to from service for example
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the report.")


@router.get("/inventory/summary", response_model=List[Dict[str, Any]])
def get_inventory_summary_report_api(
    *,
    db: Session = Depends(db_session.get_db),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Get a summary of current inventory levels and values for active products.'''
    try:
        report_data = services.reporting_service.get_inventory_summary(db)
        return report_data
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the report.")

@router.get("/financials/folio-summary", response_model=Dict[str, Any])
def get_folio_financial_summary_report_api(
    *,
    db: Session = Depends(db_session.get_db),
    date_from: date = Query(..., description="Start date for folio summary (YYYY-MM-DD)"),
    date_to: date = Query(..., description="End date for folio summary (YYYY-MM-DD)"),
    current_user: models.User = Depends(deps.require_manager_or_admin_user)
) -> Any:
    '''Get summary of total charges and payments from guest folios over a period.'''
    try:
        report_data = services.reporting_service.get_folio_financial_summary(db, date_from=date_from, date_to=date_to)
        return report_data
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="An error occurred while generating the report.")
