/**
 * Queue Management React Hooks
 * Custom hooks for queue management operations and real-time updates
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { queueApi } from '@/lib/queue-api';
import {
  Ticket,
  Service,
  Counter,
  QueueState,
  CounterState,
  QueueDashboardState,
  TicketStatus,
  CounterStatus,
  Priority
} from '@/types/queue';

// Main queue dashboard hook
export function useQueueDashboard(refreshInterval: number = 5000): QueueDashboardState {
  const [queueState, setQueueState] = useState<QueueState | null>(null);
  const [counters, setCounters] = useState<Counter[]>([]);
  const [services, setServices] = useState<Service[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCounter] = useState<string | null>(null);
  const [selectedService] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [queueData, countersData, servicesData] = await Promise.all([
        queueApi.getQueueState(selectedService || undefined),
        queueApi.getCounters(),
        queueApi.getServices(),
      ]);

      setQueueState(queueData);
      setCounters(countersData);
      setServices(servicesData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch queue data');
    } finally {
      setLoading(false);
    }
  }, [selectedService]);

  useEffect(() => {
    fetchData();

    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchData, refreshInterval]);

  return {
    queueState,
    counters,
    services,
    loading,
    error,
    selectedCounter,
    selectedService,
  };
}

// Individual counter state hook
export function useCounterState(counterId: string, refreshInterval: number = 3000): CounterState | null {
  const [counterState, setCounterState] = useState<CounterState | null>(null);
  const [, setLoading] = useState(true);
  const [, setError] = useState<string | null>(null);

  const fetchCounterState = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const state = await queueApi.getCounterState(counterId);
      setCounterState(state);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch counter state');
    } finally {
      setLoading(false);
    }
  }, [counterId, setLoading, setError]);

  useEffect(() => {
    fetchCounterState();

    const interval = setInterval(fetchCounterState, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchCounterState, refreshInterval]);

  return counterState;
}

// Ticket operations hook
export function useTicketOperations() {
  const [loading, setLoading] = useState(false);
  const [, setError] = useState<string | null>(null);

  const createTicket = useCallback(async (data: { service_id: string; customer_name?: string; customer_phone?: string; priority?: Priority }) => {
    try {
      setLoading(true);
      setError(null);
      const ticket = await queueApi.createTicket(data);
      return ticket;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to create ticket';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const startService = useCallback(async (ticketId: string) => {
    try {
      setLoading(true);
      setError(null);
      const ticket = await queueApi.startService(ticketId);
      return ticket;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to start service';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const completeService = useCallback(async (ticketId: string, satisfactionScore?: number) => {
    try {
      setLoading(true);
      setError(null);
      const ticket = await queueApi.completeService(ticketId, { satisfaction_score: satisfactionScore });
      return ticket;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to complete service';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  const cancelTicket = useCallback(async (ticketId: string, reason?: string) => {
    try {
      setLoading(true);
      setError(null);
      const ticket = await queueApi.cancelTicket(ticketId, { reason });
      return ticket;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to cancel ticket';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  return {
    createTicket,
    startService,
    completeService,
    cancelTicket,
    loading,
  };
}

// Counter operations hook
export function useCounterOperations() {
  const [loading, setLoading] = useState(false);
  const [, setError] = useState<string | null>(null);

  const callNextTicket = useCallback(async (counterId: string, operatorName?: string) => {
    try {
      setLoading(true);
      setError(null);
      const ticket = await queueApi.callNextTicket(counterId, { operator_name: operatorName });
      return ticket;
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to call next ticket';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setError]);

  return {
    callNextTicket,
    loading,
  };
}

// Waiting list hook
export function useWaitingList(serviceId?: string, limit: number = 50, refreshInterval: number = 5000): Ticket[] {
  const [waitingList, setWaitingList] = useState<Ticket[]>([]);
  const [, setLoading] = useState(true);
  const [, setError] = useState<string | null>(null);

  const fetchWaitingList = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const tickets = await queueApi.getWaitingList(serviceId, limit);
      setWaitingList(tickets);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch waiting list');
    } finally {
      setLoading(false);
    }
  }, [serviceId, limit, setLoading, setError]);

  useEffect(() => {
    fetchWaitingList();

    const interval = setInterval(fetchWaitingList, refreshInterval);
    return () => clearInterval(interval);
  }, [fetchWaitingList, refreshInterval]);

  return waitingList;
}

// Statistics hook
export function useQueueStatistics(period: string = 'today', serviceId?: string) {
  const [statistics, setStatistics] = useState<unknown>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchStatistics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const stats = await queueApi.getPerformanceMetrics(period, serviceId);
      setStatistics(stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to fetch statistics');
    } finally {
      setLoading(false);
    }
  }, [period, serviceId]);

  useEffect(() => {
    fetchStatistics();
  }, [fetchStatistics]);

  return {
    statistics,
    loading,
    error,
    refetch: fetchStatistics,
  };
}

// Real-time updates hook (WebSocket placeholder)
export function useQueueRealtimeUpdates(onUpdate?: (data: unknown) => void) {
  const [connected] = useState(false);
  const [error] = useState<string | null>(null);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    // WebSocket implementation will be added in next task
    // For now, we'll use polling as a fallback
    
    const currentWs = wsRef.current;
    
    return () => {
      if (currentWs) {
        currentWs.close();
      }
    };
  }, [onUpdate]);

  const sendMessage = useCallback((message: unknown) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(message));
    }
  }, []);

  return {
    connected,
    error,
    sendMessage,
  };
}

// Utility hook for ticket status colors
export function useTicketStatusColors() {
  const getStatusColor = useCallback((status: TicketStatus): string => {
    switch (status) {
      case TicketStatus.WAITING:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case TicketStatus.CALLED:
        return 'bg-blue-100 text-blue-800 border-blue-300';
      case TicketStatus.IN_PROGRESS:
        return 'bg-purple-100 text-purple-800 border-purple-300';
      case TicketStatus.COMPLETED:
        return 'bg-green-100 text-green-800 border-green-300';
      case TicketStatus.CANCELLED:
        return 'bg-red-100 text-red-800 border-red-300';
      case TicketStatus.NO_SHOW:
        return 'bg-gray-100 text-gray-800 border-gray-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  }, []);

  const getStatusIcon = useCallback((status: TicketStatus): string => {
    switch (status) {
      case TicketStatus.WAITING:
        return '⏳';
      case TicketStatus.CALLED:
        return '📢';
      case TicketStatus.IN_PROGRESS:
        return '⚡';
      case TicketStatus.COMPLETED:
        return '✅';
      case TicketStatus.CANCELLED:
        return '❌';
      case TicketStatus.NO_SHOW:
        return '🚫';
      default:
        return '❓';
    }
  }, []);

  return {
    getStatusColor,
    getStatusIcon,
  };
}

// Utility hook for counter status colors
export function useCounterStatusColors() {
  const getStatusColor = useCallback((status: CounterStatus): string => {
    switch (status) {
      case CounterStatus.ACTIVE:
        return 'bg-green-100 text-green-800 border-green-300';
      case CounterStatus.INACTIVE:
        return 'bg-gray-100 text-gray-800 border-gray-300';
      case CounterStatus.BREAK:
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      case CounterStatus.CLOSED:
        return 'bg-red-100 text-red-800 border-red-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  }, []);

  const getStatusIcon = useCallback((status: CounterStatus): string => {
    switch (status) {
      case CounterStatus.ACTIVE:
        return '🟢';
      case CounterStatus.INACTIVE:
        return '⚪';
      case CounterStatus.BREAK:
        return '⏸️';
      case CounterStatus.CLOSED:
        return '🔴';
      default:
        return '❓';
    }
  }, []);

  return {
    getStatusColor,
    getStatusIcon,
  };
}