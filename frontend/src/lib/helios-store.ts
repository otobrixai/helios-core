import { create } from 'zustand';
import { 
  MeasurementSessionData, 
  AnalysisSessionData, 
  HeliosSessionExport
} from '../types/stateless';

interface HeliosState {
  measurements: MeasurementSessionData[];
  analyses: AnalysisSessionData[];
  currentMeasurementId: string | null;
  currentAnalysisId: string | null;
  isLoading: boolean;
  error: string | null;

  // Actions
  addMeasurement: (measurement: MeasurementSessionData) => void;
  addAnalysis: (analysis: AnalysisSessionData) => void;
  setCurrentMeasurement: (id: string | null) => void;
  setCurrentAnalysis: (id: string | null) => void;
  clearSession: () => void;
  setError: (error: string | null) => void;
  setLoading: (isLoading: boolean) => void;
  
  // Persistence
  exportSession: () => HeliosSessionExport;
  importSession: (data: HeliosSessionExport) => void;
}

export const useHeliosStore = create<HeliosState>((set, get) => ({
  measurements: [],
  analyses: [],
  currentMeasurementId: null,
  currentAnalysisId: null,
  isLoading: false,
  error: null,

  addMeasurement: (measurement) => set((state) => ({
    measurements: [...state.measurements, measurement],
    currentMeasurementId: measurement.id
  })),

  addAnalysis: (analysis) => set((state) => ({
    analyses: [...state.analyses, analysis],
    currentAnalysisId: analysis.id
  })),

  setCurrentMeasurement: (id) => set({ currentMeasurementId: id }),
  setCurrentAnalysis: (id) => set({ currentAnalysisId: id }),

  clearSession: () => set({
    measurements: [],
    analyses: [],
    currentMeasurementId: null,
    currentAnalysisId: null,
    error: null
  }),

  setError: (error) => set({ error }),
  setLoading: (isLoading) => set({ isLoading }),

  exportSession: () => {
    const { measurements, analyses } = get();
    return {
      version: 'helios_v1.0',
      exportTimestamp: new Date().toISOString(),
      measurements,
      analyses
    };
  },

  importSession: (data) => {
    if (data.version !== 'helios_v1.0') {
      throw new Error('Unsupported session version');
    }
    set({
      measurements: data.measurements,
      analyses: data.analyses,
      currentMeasurementId: data.measurements[0]?.id || null,
      currentAnalysisId: data.analyses[0]?.id || null,
      error: null
    });
  }
}));
