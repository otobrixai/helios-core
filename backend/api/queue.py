"""
Helios Core — Queue Management API

REST API endpoints for queue management operations.
Follows FastAPI patterns with proper OpenAPI documentation.
"""

from datetime import datetime
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, Query, Depends
from pydantic import BaseModel, Field

from backend.services.queue_service import QueueService
from backend.models.queue_entities import (
    Service, Counter, Ticket, QueueState, CounterState,
    ServiceType, CounterStatus, TicketStatus, Priority
)

# Dependency injection
def get_queue_service() -> QueueService:
    """Get queue service instance."""
    return QueueService()

# Request/Response models
class CreateServiceRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    service_type: ServiceType
    description: str = Field(..., min_length=1, max_length=500)
    prefix: str = Field(..., min_length=1, max_length=5, pattern=r"^[A-Z0-9]+$")
    estimated_duration_minutes: int = Field(5, ge=1, le=120)
    priority_default: Priority = Priority.NORMAL

class CreateCounterRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    number: str = Field(..., min_length=1, max_length=10)
    location: str = Field(..., min_length=1, max_length=200)
    services_offered: List[UUID] = Field(default_factory=list)
    current_operator: Optional[str] = None

class CreateTicketRequest(BaseModel):
    service_id: UUID
    customer_name: Optional[str] = Field(None, max_length=100)
    customer_phone: Optional[str] = Field(None, max_length=20)
    customer_email: Optional[str] = Field(None, max_length=100)
    priority: Optional[Priority] = None
    notes: Optional[str] = Field(None, max_length=500)
    custom_data: dict = Field(default_factory=dict)

class CallNextTicketRequest(BaseModel):
    operator_name: Optional[str] = None

class CompleteTicketRequest(BaseModel):
    satisfaction_score: Optional[int] = Field(None, ge=1, le=5)

class CancelTicketRequest(BaseModel):
    reason: Optional[str] = Field(None, max_length=200)

# Router setup
router = APIRouter()

# =============================================================================
# SERVICE MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/services", response_model=Service, tags=["Services"])
async def create_service(
    request: CreateServiceRequest,
    service: QueueService = Depends(get_queue_service)
):
    """Create a new service type."""
    try:
        return service.create_service(request.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/services", response_model=List[Service], tags=["Services"])
async def get_services(
    service: QueueService = Depends(get_queue_service)
):
    """Get all active services."""
    # TODO: Implement service listing
    return []

@router.get("/services/{service_id}", response_model=Service, tags=["Services"])
async def get_service(
    service_id: UUID,
    service: QueueService = Depends(get_queue_service)
):
    """Get service by ID."""
    result = service._get_service(service_id)
    if not result:
        raise HTTPException(status_code=404, detail="Service not found")
    return result

# =============================================================================
# COUNTER MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/counters", response_model=Counter, tags=["Counters"])
async def create_counter(
    request: CreateCounterRequest,
    service: QueueService = Depends(get_queue_service)
):
    """Create a new service counter."""
    try:
        return service.create_counter(request.dict())
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/counters", response_model=List[Counter], tags=["Counters"])
async def get_counters(
    service: QueueService = Depends(get_queue_service)
):
    """Get all counters."""
    # TODO: Implement counter listing
    return []

@router.get("/counters/{counter_id}", response_model=Counter, tags=["Counters"])
async def get_counter(
    counter_id: UUID,
    service: QueueService = Depends(get_queue_service)
):
    """Get counter by ID."""
    result = service._get_counter(counter_id)
    if not result:
        raise HTTPException(status_code=404, detail="Counter not found")
    return result

@router.get("/counters/{counter_id}/state", response_model=CounterState, tags=["Counters"])
async def get_counter_state(
    counter_id: UUID,
    service: QueueService = Depends(get_queue_service)
):
    """Get current counter state."""
    try:
        return service.get_counter_state(counter_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# TICKET MANAGEMENT ENDPOINTS
# =============================================================================

@router.post("/tickets", response_model=Ticket, tags=["Tickets"])
async def create_ticket(
    request: CreateTicketRequest,
    service: QueueService = Depends(get_queue_service)
):
    """Generate a new ticket."""
    try:
        customer_data = {
            "name": request.customer_name,
            "phone": request.customer_phone,
            "email": request.customer_email,
            "priority": request.priority,
            "notes": request.notes,
            "custom_data": request.custom_data
        }
        return service.generate_ticket(request.service_id, customer_data)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/tickets/{ticket_id}", response_model=Ticket, tags=["Tickets"])
async def get_ticket(
    ticket_id: UUID,
    service: QueueService = Depends(get_queue_service)
):
    """Get ticket by ID."""
    result = service._get_ticket_by_id(ticket_id)
    if not result:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return result

@router.post("/tickets/{ticket_id}/start", response_model=Ticket, tags=["Tickets"])
async def start_service(
    ticket_id: UUID,
    service: QueueService = Depends(get_queue_service)
):
    """Start servicing a ticket."""
    try:
        return service.start_service(ticket_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tickets/{ticket_id}/complete", response_model=Ticket, tags=["Tickets"])
async def complete_service(
    ticket_id: UUID,
    request: CompleteTicketRequest,
    service: QueueService = Depends(get_queue_service)
):
    """Complete ticket service."""
    try:
        return service.complete_service(ticket_id, request.satisfaction_score)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/tickets/{ticket_id}/cancel", response_model=Ticket, tags=["Tickets"])
async def cancel_ticket(
    ticket_id: UUID,
    request: CancelTicketRequest,
    service: QueueService = Depends(get_queue_service)
):
    """Cancel a ticket."""
    try:
        return service.cancel_ticket(ticket_id, request.reason)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# QUEUE MANAGEMENT ENDPOINTS
# =============================================================================

@router.get("/queue/state", response_model=QueueState, tags=["Queue"])
async def get_queue_state(
    service_id: Optional[UUID] = Query(None, description="Filter by service ID"),
    service: QueueService = Depends(get_queue_service)
):
    """Get current queue state."""
    try:
        return service.get_queue_state(service_id)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/queue/waiting", response_model=List[Ticket], tags=["Queue"])
async def get_waiting_list(
    service_id: Optional[UUID] = Query(None, description="Filter by service ID"),
    limit: int = Query(50, ge=1, le=200, description="Maximum number of tickets"),
    service: QueueService = Depends(get_queue_service)
):
    """Get current waiting list."""
    try:
        return service.get_waiting_list(service_id, limit)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/counters/{counter_id}/call-next", response_model=Optional[Ticket], tags=["Queue"])
async def call_next_ticket(
    counter_id: UUID,
    request: CallNextTicketRequest,
    service: QueueService = Depends(get_queue_service)
):
    """Call the next ticket for a counter."""
    try:
        return service.call_next_ticket(counter_id, request.operator_name)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# =============================================================================
# STATISTICS ENDPOINTS
# =============================================================================

@router.get("/statistics/daily", tags=["Statistics"])
async def get_daily_statistics(
    date: Optional[datetime] = Query(None, description="Date for statistics (default: today)"),
    service_id: Optional[UUID] = Query(None, description="Filter by service ID"),
    service: QueueService = Depends(get_queue_service)
):
    """Get daily statistics."""
    # TODO: Implement statistics endpoint
    return {"message": "Statistics endpoint not yet implemented"}

@router.get("/statistics/performance", tags=["Statistics"])
async def get_performance_metrics(
    period: str = Query("today", description="Period: today, week, month"),
    service_id: Optional[UUID] = Query(None, description="Filter by service ID"),
    service: QueueService = Depends(get_queue_service)
):
    """Get performance metrics."""
    # TODO: Implement performance metrics
    return {"message": "Performance metrics endpoint not yet implemented"}

# =============================================================================
# HEALTH CHECK
# =============================================================================

@router.get("/queue/health", tags=["Health"])
async def queue_health_check(service: QueueService = Depends(get_queue_service)):
    """Queue system health check."""
    try:
        # Test database connection
        with service._get_connection() as conn:
            conn.execute("SELECT 1")
        
        return {
            "status": "healthy",
            "database": "connected",
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Service unhealthy: {str(e)}")