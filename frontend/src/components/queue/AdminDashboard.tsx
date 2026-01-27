/**
 * Admin Dashboard - Main Component
 * Primary dashboard for queue management with real-time updates
 */

'use client';

import React, { useState } from 'react';
import { 
  Users, 
  Monitor, 
  Ticket, 
  Clock, 
  Activity,
  Settings,
  RefreshCw
} from 'lucide-react';

import { useQueueDashboard } from '@/hooks/useQueueManagement';
import { CounterStatus } from '@/types/queue';
// import TicketList from './TicketList';
// import CounterGrid from './CounterGrid';
// import QueueMetrics from './QueueMetrics';
// import CreateTicketModal from './CreateTicketModal';
// import ServiceSelector from './ServiceSelector';

const AdminDashboard: React.FC = () => {
  const [autoRefresh, setAutoRefresh] = useState(true);
  
  const dashboard = useQueueDashboard(autoRefresh ? 5000 : 0);

  const handleRefresh = () => {
    // Force refresh by re-fetching data
    window.location.reload();
  };

  const getStatusCounts = () => {
    if (!dashboard.queueState) return { waiting: 0, serving: 0, completed: 0 };
    
    const waiting = dashboard.queueState.waiting_tickets.length;
    const serving = dashboard.queueState.currently_serving.length;
    
    return { waiting, serving, completed: 0 }; // TODO: Get completed count from API
  };

  const getActiveCounters = () => {
    return dashboard.counters.filter(counter => counter.status === CounterStatus.ACTIVE).length;
  };

  if (dashboard.loading && !dashboard.queueState) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  if (dashboard.error) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center max-w-md">
          <div className="text-red-500 mb-4">
            <Activity className="h-12 w-12 mx-auto" />
          </div>
          <h2 className="text-xl font-semibold text-gray-900 mb-2">Error Loading Dashboard</h2>
          <p className="text-gray-600 mb-4">{dashboard.error}</p>
          <button
            onClick={handleRefresh}
            className="bg-blue-500 text-white px-4 py-2 rounded-lg hover:bg-blue-600"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  const statusCounts = getStatusCounts();
  const activeCounters = getActiveCounters();

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center">
              <Users className="h-8 w-8 text-blue-500 mr-3" />
              <h1 className="text-xl font-semibold text-gray-900">Queue Management Dashboard</h1>
            </div>
            
            <div className="flex items-center space-x-4">
              {/* Service Filter */}
              {/* <ServiceSelector
                services={dashboard.services}
                selectedServiceId={selectedServiceId}
                onServiceChange={(serviceId: string) => {
                  setSelectedServiceId(serviceId);
                  // Update dashboard to filter by service
                }}
              /> */}
              
              {/* Auto-refresh toggle */}
              <label className="flex items-center cursor-pointer">
                <input
                  type="checkbox"
                  checked={autoRefresh}
                  onChange={(e) => setAutoRefresh(e.target.checked)}
                  className="mr-2"
                />
                <span className="text-sm text-gray-600">Auto-refresh</span>
              </label>
              
              {/* Manual refresh */}
              <button
                onClick={handleRefresh}
                className="p-2 text-gray-500 hover:text-gray-700"
                title="Refresh"
              >
                <RefreshCw className="h-5 w-5" />
              </button>
              
              {/* Settings */}
              <button className="p-2 text-gray-500 hover:text-gray-700" title="Settings">
                <Settings className="h-5 w-5" />
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats Overview */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="shrink-0">
                <Users className="h-8 w-8 text-blue-500" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Waiting</p>
                <p className="text-2xl font-semibold text-gray-900">{statusCounts.waiting}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="shrink-0">
                <Monitor className="h-8 w-8 text-green-500" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Active Counters</p>
                <p className="text-2xl font-semibold text-gray-900">{activeCounters}/{dashboard.counters.length}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="shrink-0">
                <Activity className="h-8 w-8 text-purple-500" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Currently Serving</p>
                <p className="text-2xl font-semibold text-gray-900">{statusCounts.serving}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center">
              <div className="shrink-0">
                <Clock className="h-8 w-8 text-orange-500" />
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Avg Wait Time</p>
                <p className="text-2xl font-semibold text-gray-900">
                  {dashboard.queueState ? `${dashboard.queueState.average_wait_time_minutes.toFixed(1)}m` : 'N/A'}
                </p>
              </div>
            </div>
          </div>
        </div>

              {/* Action Buttons */}
        <div className="mb-6 flex justify-between items-center">
          <div className="flex space-x-4">
            <button
              onClick={() => {}}
              disabled
              className="bg-gray-300 text-white px-4 py-2 rounded-lg flex items-center cursor-not-allowed opacity-50"
            >
              <Ticket className="h-4 w-4 mr-2" />
              Create Ticket (Disabled)
            </button>
          </div>

          <div className="flex items-center space-x-2 text-sm text-gray-500">
            {autoRefresh && (
              <>
                <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                <span>Live updates</span>
              </>
            )}
          </div>
        </div>

        {/* Main Grid Layout */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Counter Grid - Left side */}
          <div className="lg:col-span-2">
            <div className="bg-white rounded-lg shadow p-8 text-center text-gray-400 italic">
              Counter Management temporarily disabled (Build Isolation)
            </div>
            {/* <CounterGrid
              counters={dashboard.counters}
              selectedServiceId={selectedServiceId}
              onCallNext={handleCallNextTicket}
              onStartService={handleStartService}
              onCompleteService={handleCompleteService}
              onCancelTicket={handleCancelTicket}
            /> */}
          </div>

          {/* Right Sidebar */}
          <div className="space-y-6">
            {/* Queue Metrics */}
            <div className="bg-white rounded-lg shadow p-6 text-center text-gray-400 text-xs italic">
              Metrics unavailable
            </div>
            {/* <QueueMetrics
              queueState={dashboard.queueState}
              services={dashboard.services}
            /> */}

            {/* Waiting List */}
            <div className="bg-white rounded-lg shadow">
              <div className="px-6 py-4 border-b">
                <h3 className="text-lg font-medium text-gray-900">Waiting List</h3>
              </div>
              <div className="p-8 text-center text-gray-400 text-xs italic">
                Waitlist viewer disabled
              </div>
              {/* <div className="p-4">
                <TicketList
                  tickets={dashboard.queueState?.waiting_tickets || []}
                  showActions={false}
                  compact={true}
                />
              </div> */}
            </div>
          </div>
        </div>
      </main>

      {/* Create Ticket Modal */}
      {/* {showCreateTicket && (
        <CreateTicketModal
          services={dashboard.services}
          onClose={() => setShowCreateTicket(false)}
          onCreateTicket={handleCreateTicket}
        />
      )} */}
    </div>
  );
};

export default AdminDashboard;