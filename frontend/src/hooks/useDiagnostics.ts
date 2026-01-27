// frontend/src/hooks/useDiagnostics.ts
import { useState, useEffect, useCallback } from 'react';
import { FullDiagnosticReport } from '../types/diagnostics';

export const useDiagnostics = (analysisId: string | null) => {
  const [diagnostics, setDiagnostics] = useState<FullDiagnosticReport | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  const fetchDiagnostics = useCallback(async () => {
    // Skip fetching for stateless analysis IDs (which don't exist in the DB)
    if (!analysisId || analysisId.startsWith('ana_')) {
      setDiagnostics(null);
      return;
    }
    
    setLoading(true);
    setError(null);
    
    try {
      const response = await fetch(`/api/diagnostics/${analysisId}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch diagnostics: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      // Verification logic could be added here for SHA-256 validation
      // But for now we trust the backend delivery
      
      setDiagnostics(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Failed to load diagnostics:', err);
    } finally {
      setLoading(false);
    }
  }, [analysisId]);
  
  useEffect(() => {
    fetchDiagnostics();
  }, [fetchDiagnostics]);
  
  return {
    diagnostics,
    loading,
    error,
    refetch: fetchDiagnostics,
    clear: () => setDiagnostics(null)
  };
};
