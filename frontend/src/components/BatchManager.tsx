"use client";

import { AnalysisMode, MeasurementSessionData } from "@/types/stateless";

interface BatchManagerProps {
  measurements: MeasurementSessionData[];
  selectedId?: string | null;
  onSelect: (id: string) => void;
  mode: AnalysisMode;
}

export function BatchManager({
  measurements,
  selectedId,
  onSelect,
  mode,
}: BatchManagerProps) {
  // Group measurements by file hash (equivalent to substrate)
  const grouped = measurements.reduce((acc, m) => {
    const key = m.fileHash;
    if (!acc[key]) acc[key] = [];
    acc[key].push(m);
    return acc;
  }, {} as Record<string, MeasurementSessionData[]>);

  const isReference = mode === "Reference";

  return (
    <div className="p-3">
      <h2 className="text-xs font-semibold text-(--text-muted) uppercase tracking-wider mb-3 px-2">
        Batch Manager
      </h2>

      {measurements.length === 0 ? (
        <div className="text-center py-8 text-(--text-muted) text-sm">
          No files imported yet
        </div>
      ) : measurements.length > 30 ? (
        <div className="flex-1 overflow-hidden">
          {/* Note: IntegrityVirtualList would also need an update for stateless types if used */}
          <div className="text-xs text-center text-red-500 p-2">Virtual list requires update</div>
        </div>
      ) : (
        <div className="space-y-2">
          {Object.entries(grouped).map(([hash, items]) => (
            <div key={hash} className="space-y-1">
              {/* Substrate Header */}
              <div className="flex items-center gap-2 px-2 py-1">
                <svg
                  className="w-4 h-4 text-(--text-muted)"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                  />
                </svg>
                <span className="text-xs text-(--text-secondary) truncate">
                  {items[0].filename}
                </span>
              </div>

              {/* Pixel List */}
              {items.map((measurement) => (
                <button
                  key={measurement.id}
                  onClick={() => onSelect(measurement.id)}
                  className={`
                    w-full flex items-center gap-2 px-3 py-2 rounded-lg text-left
                    transition-all duration-150
                    ${
                      selectedId === measurement.id
                        ? isReference
                          ? "bg-(--accent-gold)/10 border border-(--accent-gold)/30 text-(--accent-gold)"
                          : "bg-(--accent-cyan)/10 border border-(--accent-cyan)/30 text-(--accent-cyan)"
                        : "hover:bg-(--bg-tertiary) text-(--text-secondary)"
                    }
                  `}
                >
                  {/* Pixel Icon */}
                  <span
                    className={`w-2 h-2 rounded-full ${
                      selectedId === measurement.id
                        ? isReference
                          ? "bg-(--accent-gold)"
                          : "bg-(--accent-cyan)"
                        : "bg-(--text-muted)"
                    }`}
                  />
                  <span className="text-sm truncate flex-1">
                    {measurement.deviceLabel}
                  </span>

                  {/* Mode indicator */}
                  {selectedId === measurement.id && (
                    <span
                      className={`text-[10px] px-1.5 py-0.5 rounded ${
                        isReference
                          ? "bg-(--accent-gold)/20 text-(--accent-gold)"
                          : "bg-(--accent-cyan)/20 text-(--accent-cyan)"
                      }`}
                    >
                      {isReference ? "REF" : "EXP"}
                    </span>
                  )}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
