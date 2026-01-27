/**
 * Queue Management System Types
 * TypeScript definitions for queue management entities and API responses
 */

export interface Ticket {
  id: string;
  ticket_number: string;
  service_id: string;
  customer_name?: string;
  customer_phone?: string;
  customer_email?: string;
  status: TicketStatus;
  priority: Priority;
  created_at: string;
  called_at?: string;
  service_started_at?: string;
  completed_at?: string;
  counter_id?: string;
  called_by?: string;
  notes?: string;
  custom_data: Record<string, unknown>;
}

export interface Service {
  id: string;
  name: string;
  service_type: ServiceType;
  description: string;
  prefix: string;
  estimated_duration_minutes: number;
  priority_default: Priority;
  is_active: boolean;
  created_at: string;
}

export interface Counter {
  id: string;
  name: string;
  number: string;
  location: string;
  status: CounterStatus;
  services_offered: string[];
  current_operator?: string;
  opened_at?: string;
}

export interface QueueState {
  queue_id: string;
  timestamp: string;
  waiting_tickets: Ticket[];
  currently_serving: Ticket[];
  average_wait_time_minutes: number;
  estimated_wait_time_new_ticket: number;
  counters_status: Array<{
    counter_id: string;
    name: string;
    number: string;
    status: CounterStatus;
    current_operator?: string;
  }>;
}

export interface CounterState {
  counter_id: string;
  timestamp: string;
  status: CounterStatus;
  current_ticket?: Ticket;
  next_ticket_number?: string;
  operator_name?: string;
  service_time_minutes?: number;
}

// Enums
export enum TicketStatus {
  WAITING = 'waiting',
  CALLED = 'called',
  IN_PROGRESS = 'in_progress',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
  NO_SHOW = 'no_show'
}

export enum CounterStatus {
  ACTIVE = 'active',
  INACTIVE = 'inactive',
  BREAK = 'break',
  CLOSED = 'closed'
}

export enum ServiceType {
  GENERAL = 'general',
  PRIORITY = 'priority',
  EXPRESS = 'express',
  CONSULTATION = 'consultation'
}

export enum Priority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

// API Request Types
export interface CreateServiceRequest {
  name: string;
  service_type: ServiceType;
  description: string;
  prefix: string;
  estimated_duration_minutes?: number;
  priority_default?: Priority;
}

export interface CreateCounterRequest {
  name: string;
  number: string;
  location: string;
  services_offered?: string[];
  current_operator?: string;
}

export interface CreateTicketRequest {
  service_id: string;
  customer_name?: string;
  customer_phone?: string;
  customer_email?: string;
  priority?: Priority;
  notes?: string;
  custom_data?: Record<string, unknown>;
}

export interface CallNextTicketRequest {
  operator_name?: string;
}

export interface CompleteTicketRequest {
  satisfaction_score?: number;
}

export interface CancelTicketRequest {
  reason?: string;
}

// UI State Types
export interface QueueDashboardState {
  queueState: QueueState | null;
  counters: Counter[];
  services: Service[];
  loading: boolean;
  error: string | null;
  selectedCounter: string | null;
  selectedService: string | null;
}

export interface CounterViewProps {
  counter: Counter;
  counterState?: CounterState;
  onCallNext: (counterId: string, operatorName?: string) => void;
  onStartService: (ticketId: string) => void;
  onCompleteService: (ticketId: string, satisfactionScore?: number) => void;
  onCancelTicket: (ticketId: string, reason?: string) => void;
}

export interface TicketListItemProps {
  ticket: Ticket;
  showActions?: boolean;
  onStartService?: (ticketId: string) => void;
  onCompleteService?: (ticketId: string, satisfactionScore?: number) => void;
  onCancelTicket?: (ticketId: string, reason?: string) => void;
}

// Real-time Updates
export interface QueueUpdateEvent {
  type: 'ticket_created' | 'ticket_called' | 'ticket_started' | 'ticket_completed' | 'ticket_cancelled' | 'counter_updated';
  timestamp: string;
  data: Ticket | Counter | QueueState;
}

// Statistics Types
export interface DailyStatistics {
  date: string;
  service_id: string;
  total_tickets: number;
  completed_tickets: number;
  cancelled_tickets: number;
  no_show_tickets: number;
  average_wait_time_minutes: number;
  average_service_time_minutes: number;
  peak_hour_tickets: number;
  peak_hour_start: number;
}

export interface ServiceMetrics {
  service_id: string;
  period_start: string;
  period_end: string;
  total_tickets: number;
  completed_tickets: number;
  completion_rate: number;
  average_wait_time_minutes: number;
  median_wait_time_minutes: number;
  max_wait_time_minutes: number;
  average_service_time_minutes: number;
  median_service_time_minutes: number;
  tickets_cancelled: number;
  tickets_no_show: number;
  customer_satisfaction_score?: number;
}