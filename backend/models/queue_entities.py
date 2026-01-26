"""
Helios Core — Queue Management Entity Models

Pydantic schemas for Queue, Ticket, Counter, and Service entities.
Follows existing Helios Core patterns with proper immutability and deterministic design.
"""

from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, ConfigDict


# =============================================================================
# ENUMS
# =============================================================================

class TicketStatus(str, Enum):
    """Ticket status states."""
    WAITING = "waiting"
    CALLED = "called"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"

class CounterStatus(str, Enum):
    """Counter operational status."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BREAK = "break"
    CLOSED = "closed"

class ServiceType(str, Enum):
    """Service categories."""
    GENERAL = "general"
    PRIORITY = "priority"
    EXPRESS = "express"
    CONSULTATION = "consultation"

class Priority(str, Enum):
    """Ticket priority levels."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"


# =============================================================================
# SERVICE ENTITY
# =============================================================================

class Service(BaseModel):
    """
    Service type configuration.
    Defines the categories of services available in the queue system.
    """
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    service_type: ServiceType
    description: str
    prefix: str  # Ticket prefix (e.g., "A", "B", "C")
    estimated_duration_minutes: int = 5
    priority_default: Priority = Priority.NORMAL
    is_active: bool = True
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# COUNTER ENTITY
# =============================================================================

class Counter(BaseModel):
    """
    Service counter configuration.
    Represents physical or virtual service points.
    """
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    number: str  # Display number (e.g., "1", "2", "A")
    location: str
    status: CounterStatus = CounterStatus.INACTIVE
    services_offered: List[UUID] = Field(default_factory=list)  # Service IDs
    current_operator: Optional[str] = None
    opened_at: Optional[datetime] = None


# =============================================================================
# TICKET ENTITY
# =============================================================================

class Ticket(BaseModel):
    """
    Individual customer ticket.
    Core entity representing a customer's place in queue.
    """
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    ticket_number: str  # e.g., "A001", "B045"
    service_id: UUID
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    status: TicketStatus = TicketStatus.WAITING
    priority: Priority = Priority.NORMAL
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    called_at: Optional[datetime] = None
    service_started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Service assignment
    counter_id: Optional[UUID] = None
    called_by: Optional[str] = None
    
    # Notes and metadata
    notes: Optional[str] = None
    custom_data: dict = Field(default_factory=dict)


# =============================================================================
# QUEUE ENTITY
# =============================================================================

class Queue(BaseModel):
    """
    Queue configuration and statistics.
    Represents a logical queue for a service or group of services.
    """
    model_config = ConfigDict(frozen=True)
    
    id: UUID = Field(default_factory=uuid4)
    name: str
    service_ids: List[UUID]  # Services included in this queue
    description: str
    
    # Configuration
    max_wait_time_minutes: int = 60
    auto_call_interval_seconds: int = 30
    is_active: bool = True
    
    # Statistics (computed fields, not persisted)
    average_wait_time_minutes: Optional[float] = None
    currently_waiting: int = 0
    total_served_today: int = 0
    
    created_at: datetime = Field(default_factory=datetime.utcnow)


# =============================================================================
# REAL-TIME STATE MODELS
# =============================================================================

class QueueState(BaseModel):
    """
    Real-time snapshot of queue state.
    Used for WebSocket updates and dashboard displays.
    """
    queue_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    waiting_tickets: List[Ticket]
    currently_serving: List[Ticket]
    average_wait_time_minutes: float
    estimated_wait_time_new_ticket: int
    counters_status: List[dict]


class CounterState(BaseModel):
    """
    Real-time counter state.
    Current ticket being served and counter status.
    """
    counter_id: UUID
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    status: CounterStatus
    current_ticket: Optional[Ticket] = None
    next_ticket_number: Optional[str] = None
    operator_name: Optional[str] = None
    service_time_minutes: Optional[float] = None


# =============================================================================
# ANALYTICS MODELS
# =============================================================================

class DailyStatistics(BaseModel):
    """
    Daily performance statistics.
    """
    date: datetime
    service_id: UUID
    total_tickets: int
    completed_tickets: int
    cancelled_tickets: int
    no_show_tickets: int
    average_wait_time_minutes: float
    average_service_time_minutes: float
    peak_hour_tickets: int
    peak_hour_start: int


class ServiceMetrics(BaseModel):
    """
    Service performance metrics.
    """
    service_id: UUID
    period_start: datetime
    period_end: datetime
    
    # Basic metrics
    total_tickets: int
    completed_tickets: int
    completion_rate: float
    
    # Time metrics
    average_wait_time_minutes: float
    median_wait_time_minutes: float
    max_wait_time_minutes: int
    
    average_service_time_minutes: float
    median_service_time_minutes: float
    
    # Satisfaction metrics
    tickets_cancelled: int
    tickets_no_show: int
    customer_satisfaction_score: Optional[float] = None


# =============================================================================
# DATABASE TABLE SCHEMAS (for SQLite)
# =============================================================================

SERVICES_TABLE = """
CREATE TABLE IF NOT EXISTS services (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    service_type TEXT NOT NULL,
    description TEXT NOT NULL,
    prefix TEXT NOT NULL UNIQUE,
    estimated_duration_minutes INTEGER NOT NULL DEFAULT 5,
    priority_default TEXT NOT NULL DEFAULT 'normal',
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
"""

COUNTERS_TABLE = """
CREATE TABLE IF NOT EXISTS counters (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    number TEXT NOT NULL UNIQUE,
    location TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'inactive',
    services_offered TEXT NOT NULL DEFAULT '[]',
    current_operator TEXT,
    opened_at TEXT,
    UNIQUE(name, number)
);
"""

TICKETS_TABLE = """
CREATE TABLE IF NOT EXISTS tickets (
    id TEXT PRIMARY KEY,
    ticket_number TEXT NOT NULL,
    service_id TEXT NOT NULL,
    customer_name TEXT,
    customer_phone TEXT,
    customer_email TEXT,
    status TEXT NOT NULL DEFAULT 'waiting',
    priority TEXT NOT NULL DEFAULT 'normal',
    created_at TEXT NOT NULL,
    called_at TEXT,
    service_started_at TEXT,
    completed_at TEXT,
    counter_id TEXT,
    called_by TEXT,
    notes TEXT,
    custom_data TEXT NOT NULL DEFAULT '{}',
    FOREIGN KEY (service_id) REFERENCES services(id),
    FOREIGN KEY (counter_id) REFERENCES counters(id),
    UNIQUE(ticket_number)
);
"""

QUEUES_TABLE = """
CREATE TABLE IF NOT EXISTS queues (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    service_ids TEXT NOT NULL,
    description TEXT NOT NULL,
    max_wait_time_minutes INTEGER NOT NULL DEFAULT 60,
    auto_call_interval_seconds INTEGER NOT NULL DEFAULT 30,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL
);
"""

DAILY_STATISTICS_TABLE = """
CREATE TABLE IF NOT EXISTS daily_statistics (
    id TEXT PRIMARY KEY,
    date TEXT NOT NULL,
    service_id TEXT NOT NULL,
    total_tickets INTEGER NOT NULL,
    completed_tickets INTEGER NOT NULL,
    cancelled_tickets INTEGER NOT NULL,
    no_show_tickets INTEGER NOT NULL,
    average_wait_time_minutes REAL NOT NULL,
    average_service_time_minutes REAL NOT NULL,
    peak_hour_tickets INTEGER NOT NULL,
    peak_hour_start INTEGER NOT NULL,
    FOREIGN KEY (service_id) REFERENCES services(id),
    UNIQUE(date, service_id)
);
"""

# =============================================================================
# INDEXES FOR PERFORMANCE
# =============================================================================

TICKETS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_tickets_status ON tickets(status);",
    "CREATE INDEX IF NOT EXISTS idx_tickets_service_created ON tickets(service_id, created_at);",
    "CREATE INDEX IF NOT EXISTS idx_tickets_counter ON tickets(counter_id);",
    "CREATE INDEX IF NOT EXISTS idx_tickets_number ON tickets(ticket_number);",
]

COUNTERS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_counters_status ON counters(status);",
    "CREATE INDEX IF NOT EXISTS idx_counters_services ON counters(services_offered);",
]

STATISTICS_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_daily_stats_date ON daily_statistics(date);",
    "CREATE INDEX IF NOT EXISTS idx_daily_stats_service ON daily_statistics(service_id);",
]