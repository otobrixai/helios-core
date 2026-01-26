"""
Helios Core — Queue Management Service

Core business logic for queue operations.
Follows deterministic patterns and maintains data integrity.
"""

import json
import sqlite3
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from uuid import UUID, uuid4

from backend.models.queue_entities import (
    Ticket, TicketStatus, Counter, CounterStatus, Service, Queue,
    QueueState, CounterState, Priority, ServiceType
)


class QueueService:
    """
    Core queue management service.
    Handles ticket generation, queue logic, and real-time state.
    """
    
    def __init__(self, db_path: str = "helios_queue.db"):
        self.db_path = db_path
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize database with required tables and indexes."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA foreign_keys = ON")
            
            # Import table definitions
            from backend.models.queue_entities import (
                SERVICES_TABLE, COUNTERS_TABLE, TICKETS_TABLE, QUEUES_TABLE,
                DAILY_STATISTICS_TABLE, TICKETS_INDEXES, COUNTERS_INDEXES,
                STATISTICS_INDEXES
            )
            
            # Create tables
            conn.execute(SERVICES_TABLE)
            conn.execute(COUNTERS_TABLE)
            conn.execute(TICKETS_TABLE)
            conn.execute(QUEUES_TABLE)
            conn.execute(DAILY_STATISTICS_TABLE)
            
            # Create indexes
            for index_sql in TICKETS_INDEXES + COUNTERS_INDEXES + STATISTICS_INDEXES:
                conn.execute(index_sql)
            
            conn.commit()
    
    def create_service(self, service_data: dict) -> Service:
        """Create a new service type."""
        service = Service(**service_data)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO services 
                (id, name, service_type, description, prefix, estimated_duration_minutes,
                 priority_default, is_active, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(service.id), service.name, service.service_type,
                    service.description, service.prefix, service.estimated_duration_minutes,
                    service.priority_default, service.is_active, service.created_at.isoformat()
                )
            )
            conn.commit()
        
        return service
    
    def create_counter(self, counter_data: dict) -> Counter:
        """Create a new service counter."""
        counter = Counter(**counter_data)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO counters
                (id, name, number, location, status, services_offered, current_operator, opened_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(counter.id), counter.name, counter.number, counter.location,
                    counter.status, json.dumps(counter.services_offered),
                    counter.current_operator,
                    counter.opened_at.isoformat() if counter.opened_at else None
                )
            )
            conn.commit()
        
        return counter
    
    def generate_ticket(self, service_id: UUID, customer_data: dict = None) -> Ticket:
        """
        Generate a new ticket with sequential numbering.
        Follows deterministic ticket numbering patterns.
        """
        service = self._get_service(service_id)
        if not service:
            raise ValueError(f"Service {service_id} not found")
        
        # Generate ticket number with prefix and sequential number
        ticket_number = self._generate_ticket_number(service.prefix)
        
        ticket_data = {
            "service_id": service_id,
            "ticket_number": ticket_number,
            "customer_name": customer_data.get("name") if customer_data else None,
            "customer_phone": customer_data.get("phone") if customer_data else None,
            "customer_email": customer_data.get("email") if customer_data else None,
            "priority": customer_data.get("priority", service.priority_default) if customer_data else service.priority_default,
            "notes": customer_data.get("notes") if customer_data else None,
            "custom_data": customer_data.get("custom_data", {}) if customer_data else {}
        }
        
        ticket = Ticket(**ticket_data)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO tickets
                (id, ticket_number, service_id, customer_name, customer_phone, customer_email,
                 status, priority, created_at, called_at, service_started_at, completed_at,
                 counter_id, called_by, notes, custom_data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    str(ticket.id), ticket.ticket_number, str(ticket.service_id),
                    ticket.customer_name, ticket.customer_phone, ticket.customer_email,
                    ticket.status, ticket.priority, ticket.created_at.isoformat(),
                    ticket.called_at.isoformat() if ticket.called_at else None,
                    ticket.service_started_at.isoformat() if ticket.service_started_at else None,
                    ticket.completed_at.isoformat() if ticket.completed_at else None,
                    str(ticket.counter_id) if ticket.counter_id else None,
                    ticket.called_by, ticket.notes, json.dumps(ticket.custom_data)
                )
            )
            conn.commit()
        
        return ticket
    
    def _generate_ticket_number(self, prefix: str) -> str:
        """Generate sequential ticket number for service prefix."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT ticket_number FROM tickets WHERE ticket_number LIKE ? ORDER BY ticket_number DESC LIMIT 1",
                (f"{prefix}%",)
            )
            result = cursor.fetchone()
            
            if result:
                last_number = int(result[0][len(prefix):])
                next_number = last_number + 1
            else:
                next_number = 1
            
            return f"{prefix}{next_number:03d}"
    
    def call_next_ticket(self, counter_id: UUID, operator_name: str = None) -> Optional[Ticket]:
        """Call the next ticket for a counter."""
        counter = self._get_counter(counter_id)
        if not counter:
            raise ValueError(f"Counter {counter_id} not found")
        
        # Get next ticket in queue for services offered by this counter
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT t.*, s.name as service_name
                FROM tickets t
                JOIN services s ON t.service_id = s.id
                WHERE t.status = 'waiting' 
                AND s.prefix IN (SELECT prefix FROM services WHERE id IN 
                    (SELECT value FROM json_each(?) WHERE value = id))
                ORDER BY 
                    CASE t.priority 
                        WHEN 'urgent' THEN 1 
                        WHEN 'high' THEN 2 
                        WHEN 'normal' THEN 3 
                        WHEN 'low' THEN 4 
                    END,
                    t.created_at ASC
                LIMIT 1
                """,
                (json.dumps([str(sid) for sid in counter.services_offered]),)
            )
            result = cursor.fetchone()
            
            if not result:
                return None
            
            # Update ticket status
            ticket_id = result[0]
            now = datetime.utcnow()
            
            conn.execute(
                """
                UPDATE tickets 
                SET status = 'called', called_at = ?, counter_id = ?, called_by = ?
                WHERE id = ?
                """,
                (now.isoformat(), str(counter_id), operator_name, ticket_id)
            )
            conn.commit()
        
        return self._get_ticket_by_id(UUID(ticket_id))
    
    def start_service(self, ticket_id: UUID) -> Ticket:
        """Mark ticket as being serviced."""
        ticket = self._get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        if ticket.status != TicketStatus.CALLED:
            raise ValueError("Only called tickets can be started")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tickets 
                SET status = 'in_progress', service_started_at = ?
                WHERE id = ?
                """,
                (datetime.utcnow().isoformat(), str(ticket_id))
            )
            conn.commit()
        
        return self._get_ticket_by_id(ticket_id)
    
    def complete_service(self, ticket_id: UUID, satisfaction_score: int = None) -> Ticket:
        """Complete ticket service and update statistics."""
        ticket = self._get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        if ticket.status != TicketStatus.IN_PROGRESS:
            raise ValueError("Only in-progress tickets can be completed")
        
        now = datetime.utcnow()
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tickets 
                SET status = 'completed', completed_at = ?
                WHERE id = ?
                """,
                (now.isoformat(), str(ticket_id))
            )
            conn.commit()
            
            # Update daily statistics
            self._update_daily_statistics(ticket.service_id, conn)
        
        return self._get_ticket_by_id(ticket_id)
    
    def cancel_ticket(self, ticket_id: UUID, reason: str = None) -> Ticket:
        """Cancel a ticket."""
        ticket = self._get_ticket_by_id(ticket_id)
        if not ticket:
            raise ValueError(f"Ticket {ticket_id} not found")
        
        if ticket.status in [TicketStatus.COMPLETED, TicketStatus.CANCELLED]:
            raise ValueError("Cannot cancel completed or already cancelled tickets")
        
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                UPDATE tickets 
                SET status = 'cancelled', notes = COALESCE(notes, '') || ?
                WHERE id = ?
                """,
                (f"\nCancelled: {reason}" if reason else "\nCancelled", str(ticket_id))
            )
            conn.commit()
        
        return self._get_ticket_by_id(ticket_id)
    
    def get_queue_state(self, service_id: UUID = None) -> QueueState:
        """Get current real-time queue state."""
        with sqlite3.connect(self.db_path) as conn:
            # Get waiting tickets
            waiting_query = """
                SELECT t.* FROM tickets t 
                WHERE t.status = 'waiting'
            """
            params = []
            if service_id:
                waiting_query += " AND t.service_id = ?"
                params.append(str(service_id))
            
            waiting_query += " ORDER BY t.created_at ASC"
            
            waiting_tickets = []
            for row in conn.execute(waiting_query, params):
                waiting_tickets.append(self._row_to_ticket(row))
            
            # Get currently serving tickets
            serving_query = """
                SELECT t.* FROM tickets t 
                WHERE t.status IN ('called', 'in_progress')
            """
            params = []
            if service_id:
                serving_query += " AND t.service_id = ?"
                params.append(str(service_id))
            
            serving_query += " ORDER BY t.called_at ASC"
            
            currently_serving = []
            for row in conn.execute(serving_query, params):
                currently_serving.append(self._row_to_ticket(row))
            
            # Calculate wait times
            avg_wait_time = self._calculate_average_wait_time(service_id, conn)
            estimated_wait = self._estimate_wait_time_new_ticket(service_id, conn)
            
            # Get counter statuses
            counters_status = []
            for row in conn.execute("SELECT * FROM counters WHERE status = 'active'"):
                counter = self._row_to_counter(row)
                counters_status.append({
                    "counter_id": str(counter.id),
                    "name": counter.name,
                    "number": counter.number,
                    "status": counter.status,
                    "current_operator": counter.current_operator
                })
            
            return QueueState(
                queue_id=service_id or uuid4(),
                waiting_tickets=waiting_tickets,
                currently_serving=currently_serving,
                average_wait_time_minutes=avg_wait_time,
                estimated_wait_time_new_ticket=estimated_wait,
                counters_status=counters_status
            )
    
    def get_counter_state(self, counter_id: UUID) -> CounterState:
        """Get current counter state."""
        counter = self._get_counter(counter_id)
        if not counter:
            raise ValueError(f"Counter {counter_id} not found")
        
        with sqlite3.connect(self.db_path) as conn:
            # Get current ticket
            cursor = conn.execute(
                """
                SELECT t.* FROM tickets t
                WHERE t.counter_id = ? AND t.status IN ('called', 'in_progress')
                ORDER BY t.called_at DESC LIMIT 1
                """,
                (str(counter_id),)
            )
            current_row = cursor.fetchone()
            current_ticket = self._row_to_ticket(current_row) if current_row else None
            
            # Calculate service time for current ticket
            service_time = None
            if current_ticket and current_ticket.service_started_at:
                service_time = (datetime.utcnow() - current_ticket.service_started_at).total_seconds() / 60
            
            # Get next ticket
            next_ticket = self.call_next_ticket(counter_id)
            
            return CounterState(
                counter_id=counter_id,
                status=counter.status,
                current_ticket=current_ticket,
                next_ticket_number=next_ticket.ticket_number if next_ticket else None,
                operator_name=counter.current_operator,
                service_time_minutes=service_time
            )
    
    def get_waiting_list(self, service_id: UUID = None, limit: int = 50) -> List[Ticket]:
        """Get current waiting list."""
        with sqlite3.connect(self.db_path) as conn:
            query = """
                SELECT t.* FROM tickets t
                WHERE t.status = 'waiting'
            """
            params = []
            if service_id:
                query += " AND t.service_id = ?"
                params.append(str(service_id))
            
            query += " ORDER BY t.created_at ASC LIMIT ?"
            params.append(limit)
            
            waiting_tickets = []
            for row in conn.execute(query, params):
                waiting_tickets.append(self._row_to_ticket(row))
            
            return waiting_tickets
    
    # Helper methods
    def _get_service(self, service_id: UUID) -> Optional[Service]:
        """Get service by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM services WHERE id = ?", (str(service_id),))
            row = cursor.fetchone()
            return self._row_to_service(row) if row else None
    
    def _get_counter(self, counter_id: UUID) -> Optional[Counter]:
        """Get counter by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM counters WHERE id = ?", (str(counter_id),))
            row = cursor.fetchone()
            return self._row_to_counter(row) if row else None
    
    def _get_ticket_by_id(self, ticket_id: UUID) -> Optional[Ticket]:
        """Get ticket by ID."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("SELECT * FROM tickets WHERE id = ?", (str(ticket_id),))
            row = cursor.fetchone()
            return self._row_to_ticket(row) if row else None
    
    def _row_to_service(self, row) -> Service:
        """Convert database row to Service object."""
        return Service(
            id=UUID(row[0]), name=row[1], service_type=ServiceType(row[2]),
            description=row[3], prefix=row[4], estimated_duration_minutes=row[5],
            priority_default=Priority(row[6]), is_active=bool(row[7]),
            created_at=datetime.fromisoformat(row[8])
        )
    
    def _row_to_counter(self, row) -> Counter:
        """Convert database row to Counter object."""
        return Counter(
            id=UUID(row[0]), name=row[1], number=row[2], location=row[3],
            status=CounterStatus(row[4]), services_offered=json.loads(row[5]),
            current_operator=row[6],
            opened_at=datetime.fromisoformat(row[7]) if row[7] else None
        )
    
    def _row_to_ticket(self, row) -> Ticket:
        """Convert database row to Ticket object."""
        return Ticket(
            id=UUID(row[0]), ticket_number=row[1], service_id=UUID(row[2]),
            customer_name=row[3], customer_phone=row[4], customer_email=row[5],
            status=TicketStatus(row[6]), priority=Priority(row[7]),
            created_at=datetime.fromisoformat(row[8]),
            called_at=datetime.fromisoformat(row[9]) if row[9] else None,
            service_started_at=datetime.fromisoformat(row[10]) if row[10] else None,
            completed_at=datetime.fromisoformat(row[11]) if row[11] else None,
            counter_id=UUID(row[12]) if row[12] else None,
            called_by=row[13], notes=row[14], custom_data=json.loads(row[15])
        )
    
    def _calculate_average_wait_time(self, service_id: UUID, conn) -> float:
        """Calculate average wait time for completed tickets today."""
        today = datetime.utcnow().date().isoformat()
        
        cursor = conn.execute(
            """
            SELECT AVG((julianday(called_at) - julianday(created_at)) * 24 * 60)
            FROM tickets 
            WHERE status = 'completed' 
            AND DATE(created_at) = ?
            AND called_at IS NOT NULL
            """,
            (today,)
        )
        result = cursor.fetchone()
        return float(result[0]) if result[0] else 0.0
    
    def _estimate_wait_time_new_ticket(self, service_id: UUID, conn) -> int:
        """Estimate wait time for a new ticket."""
        avg_service_time = 5  # Default 5 minutes
        waiting_count = 0
        
        if service_id:
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM tickets 
                WHERE status = 'waiting' AND service_id = ?
                """,
                (str(service_id),)
            )
            waiting_count = cursor.fetchone()[0]
        else:
            cursor = conn.execute(
                "SELECT COUNT(*) FROM tickets WHERE status = 'waiting'"
            )
            waiting_count = cursor.fetchone()[0]
        
        return int(waiting_count * avg_service_time)
    
    def _update_daily_statistics(self, service_id: UUID, conn):
        """Update daily statistics for a service."""
        today = datetime.utcnow().date().isoformat()
        
        # Calculate today's statistics
        cursor = conn.execute(
            """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                SUM(CASE WHEN status = 'cancelled' THEN 1 ELSE 0 END) as cancelled,
                SUM(CASE WHEN status = 'no_show' THEN 1 ELSE 0 END) as no_show,
                AVG(CASE WHEN called_at IS NOT NULL 
                    THEN (julianday(called_at) - julianday(created_at)) * 24 * 60 
                    ELSE NULL END) as avg_wait,
                AVG(CASE WHEN completed_at IS NOT NULL AND service_started_at IS NOT NULL 
                    THEN (julianday(completed_at) - julianday(service_started_at)) * 24 * 60 
                    ELSE NULL END) as avg_service
            FROM tickets 
            WHERE service_id = ? AND DATE(created_at) = ?
            """,
            (str(service_id), today)
        )
        stats = cursor.fetchone()
        
        # Upsert statistics
        conn.execute(
            """
            INSERT OR REPLACE INTO daily_statistics
            (id, date, service_id, total_tickets, completed_tickets, cancelled_tickets,
             no_show_tickets, average_wait_time_minutes, average_service_time_minutes,
             peak_hour_tickets, peak_hour_start)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(uuid4()), today, str(service_id), stats[0], stats[1], stats[2], stats[3],
                float(stats[4]) if stats[4] else 0.0,
                float(stats[5]) if stats[5] else 0.0,
                0, 0  # TODO: Implement peak hour calculation
            )
        )