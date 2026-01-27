"use client";

import React, { useMemo } from "react";
import { List } from "react-window";
import { Shield, CheckCircle, AlertTriangle } from "lucide-react";
import { AnalysisMode, MeasurementSessionData as Measurement } from "@/types/stateless";

interface IntegrityVirtualListProps {
  measurements: Measurement[];
  selectedId?: string;
  onSelect: (measurement: Measurement) => void;
  mode: AnalysisMode;
  analysisStatus?: Record<
    string,
    "pending" | "complete" | "failed" | "validated"
  >;
  integrityHashes?: Record<string, string>;
}

export const IntegrityVirtualList: React.FC<IntegrityVirtualListProps> = ({
  measurements,
  selectedId,
  onSelect,
  mode,
  analysisStatus = {},
  integrityHashes = {},
}) => {
  const isReference = mode === "Reference";

  // Group measurements by import for organization
  const groupedData = useMemo(() => {
    return measurements.map((item) => ({
      ...item,
      groupLabel: `File: ${item.fileHash.slice(0, 8)}...`,
    }));
  }, [measurements]);

  // Row renderer with integrity indicators
  const Row = ({
    index,
    style,
  }: {
    index: number;
    style: React.CSSProperties;
  }) => {
    const measurement = groupedData[index];
    const status = analysisStatus[measurement.id] || "pending";
    const hash = integrityHashes[measurement.id];
    const isSelected = selectedId === measurement.id;

    const getStatusColor = () => {
      switch (status) {
        case "validated":
          return "text-(--accent-green)";
        case "complete":
          return isReference ? "text-(--accent-gold)" : "text-(--accent-cyan)";
        case "failed":
          return "text-(--accent-red)";
        default:
          return "text-(--text-muted)";
      }
    };

    const getStatusIcon = () => {
      switch (status) {
        case "validated":
          return <CheckCircle size={12} />;
        case "complete":
          return isReference ? <Shield size={12} /> : null;
        case "failed":
          return <AlertTriangle size={12} />;
        default:
          return null;
      }
    };

    return (
      <div style={style} className="px-2 py-1">
        <button
          onClick={() => onSelect(measurement)}
          className={`
            w-full flex items-center gap-3 px-3 py-2 border-l-4 transition-all rounded-r-lg
            ${
              isSelected
                ? isReference
                  ? "bg-(--accent-gold)/10 border-l-(--accent-gold)"
                  : "bg-(--accent-cyan)/10 border-l-(--accent-cyan)"
                : "border-l-transparent hover:bg-(--bg-tertiary)"
            }
          `}
        >
          {/* Pixel Indicator */}
          <div
            className={`w-3 h-3 rounded relative ${getStatusColor()} ${status === "complete" ? "animate-pulse" : ""}`}
            style={{ backgroundColor: 'currentColor' }}
          >
            {getStatusIcon() && (
              <div className="absolute -top-1 -right-1">{getStatusIcon()}</div>
            )}
          </div>

          {/* Measurement Info */}
          <div className="flex-1 min-w-0 text-left">
            <div className="flex items-center justify-between">
              <span className={`text-sm truncate ${isSelected ? 'font-semibold' : ''}`}>{measurement.deviceLabel}</span>
              <span className="text-[10px] text-(--text-muted)">{index + 1}</span>
            </div>
            <div className="text-[10px] text-(--text-muted) truncate">
              {measurement.groupLabel}
            </div>
          </div>

          {/* Integrity Badge */}
          {hash && (
            <div
              className="tooltip"
              data-tip={`SHA256: ${hash.substring(0, 16)}...`}
            >
              <div className="flex items-center gap-1 px-2 py-1 rounded bg-(--bg-card) border border-(--border-default)">
                <Shield size={10} className="text-(--accent-green)" />
                <span className="text-[8px] font-mono">✓</span>
              </div>
            </div>
          )}
        </button>
      </div>
    );
  };

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-(--border-default) shrink-0">
        <div className="flex items-center justify-between">
          <span className="text-xs font-semibold text-(--text-muted)">
            {measurements.length} Measurements
          </span>
          <span className="text-[10px] text-(--text-muted)">
            Virtual Scrolling Active
          </span>
        </div>
      </div>

      <div className="flex-1">
        {/* @ts-expect-error react-window 2.x API mismatch */}
        <List
          rowCount={groupedData.length}
          rowHeight={60}
          className="scrollbar-thin"
          rowComponent={Row}
          style={{ height: 500, width: '100%' }}
        />
      </div>
    </div>
  );
};
