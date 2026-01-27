import { useMemo } from 'react';
import { Info } from 'lucide-react';

interface DataPoint {
  voltage: number;
  current: number;
  current_density?: number;
  power?: number;
  fit_current?: number;
  fit_power?: number;
  residual?: number;
}

interface ScientificPlotConfig {
  maxPoints: number;
  preserveExtrema: boolean;
  smoothTolerance: number;
}

interface PlotMetadata {
  originalPoints: number;
  displayedPoints: number;
  compressionRatio: number;
  isDownsampled: boolean;
}

export const useScientificPlotData = (
  rawData: DataPoint[],
  config: ScientificPlotConfig = {
    maxPoints: 400,
    preserveExtrema: true,
    smoothTolerance: 0.001
  }
) => {
  return useMemo(() => {
    if (!rawData || rawData.length <= config.maxPoints) {
      return {
        displayData: rawData || [],
        isDownsampled: false,
        metadata: {
          originalPoints: rawData?.length || 0,
          displayedPoints: rawData?.length || 0,
          compressionRatio: 1,
          isDownsampled: false
        }
      };
    }

    // Min-Max Decimation Algorithm (Ramer-Douglas-Peucker variant)
    const downsample = (data: DataPoint[], tolerance: number): DataPoint[] => {
      const result: DataPoint[] = [];

      // Always keep first and last points
      result.push(data[0]);

      // Find important points (significant curvature, extrema)
      for (let i = 1; i < data.length - 1; i++) {
        const prev = data[i - 1];
        const curr = data[i];
        const next = data[i + 1];

        // Check if this is a local extremum
        const isLocalMax = curr.current > prev.current && curr.current > next.current;
        const isLocalMin = curr.current < prev.current && curr.current < next.current;

        // Check for significant curvature (second derivative approximation)
        const curvature = Math.abs(
          next.current - 2 * curr.current + prev.current
        );

        if (isLocalMax || isLocalMin || curvature > tolerance) {
          result.push(curr);
        }

        // Ensure we don't exceed max points
        if (result.length >= config.maxPoints) break;
      }

      // Always keep last point
      if (!result.some(p => p === data[data.length - 1])) {
        result.push(data[data.length - 1]);
      }

      // Fill gaps to ensure smooth visualization if we have fewer points than requested
      const finalTarget = Math.min(config.maxPoints, data.length);
      if (result.length < finalTarget) {
        const remainingNeeded = finalTarget - result.length;
        const step = Math.max(1, Math.floor(data.length / remainingNeeded));
        for (let i = 0; i < data.length && result.length < finalTarget; i += step) {
          if (!result.some(p => p.voltage === data[i].voltage)) {
            result.push(data[i]);
          }
        }
        result.sort((a, b) => a.voltage - b.voltage);
      }

      return result.slice(0, finalTarget);
    };

    const displayData = downsample(rawData, config.smoothTolerance);

    return {
      displayData,
      isDownsampled: true,
      metadata: {
        originalPoints: rawData.length,
        displayedPoints: displayData.length,
        compressionRatio: rawData.length / displayData.length,
        extremaPreserved: config.preserveExtrema,
        algorithm: 'min-max-decimation',
        isDownsampled: true
      }
    };
  }, [rawData, config.maxPoints, config.preserveExtrema, config.smoothTolerance]);
};

// Component to show decimation status
export const PlotIntegrityBadge: React.FC<{ metadata: PlotMetadata }> = ({ metadata }) => {
  if (!metadata || !metadata.isDownsampled) return null;

  return (
    <div className="absolute top-2 right-2 z-20">
      <div className="flex items-center gap-2 px-2 py-1 bg-(--bg-tertiary)/80 backdrop-blur-sm rounded-lg border border-(--border-default)">
        <div className="w-2 h-2 rounded-full bg-(--accent-cyan) animate-pulse" />
        <span className="text-[9px] font-mono text-(--text-secondary)">
          {metadata.displayedPoints}/{metadata.originalPoints} pts
        </span>
        <div className="tooltip" data-tip="Min-Max decimation preserves critical features">
          <Info size={10} className="text-(--text-muted)" />
        </div>
      </div>
    </div>
  );
};
