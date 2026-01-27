"use client";

import React from 'react';
import { AnalysisMode } from '@/types/stateless';

interface SkeletonConfig {
  type: 'chart' | 'metrics' | 'diagnostics' | 'table';
  mode: AnalysisMode;
  hasData: boolean;
}

export const ScientificSkeleton: React.FC<SkeletonConfig> = ({ type, mode, hasData }) => {
  const isReference = mode === 'Reference';

  if (hasData) return null;

  const getSkeleton = () => {
    switch (type) {
      case 'chart':
        return (
          <div className="relative h-full bg-(--bg-tertiary) rounded-lg overflow-hidden border border-(--border-default)">
            {/* Animated grid lines */}
            <div className="absolute inset-0 opacity-10">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="absolute h-px w-full bg-white" style={{ top: `${(i + 1) * 20}%` }} />
              ))}
              {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="absolute w-px h-full bg-white" style={{ left: `${(i + 1) * 12.5}%` }} />
              ))}
            </div>

            {/* Animated scan line */}
            <div className="absolute top-0 left-0 w-full h-0.5 bg-(--accent-cyan) animate-scan" />

            {/* Loading indicator */}
            <div className="absolute top-4 right-4">
              <div className="flex items-center gap-2 px-3 py-2 bg-(--bg-card)/80 backdrop-blur-sm rounded-lg">
                <div className="w-3 h-3 rounded-full border-2 border-(--accent-cyan) border-t-transparent animate-spin" />
                <span className="text-xs font-mono text-(--text-muted)">
                  {isReference ? 'REFERENCE MODE' : 'LOADING DATA'}
                </span>
              </div>
            </div>
          </div>
        );

      case 'metrics':
        return (
          <div className="grid grid-cols-2 gap-3">
            {Array.from({ length: 4 }).map((_, i) => (
              <div key={i} className="metric-card">
                <div className="h-6 bg-(--bg-tertiary) rounded animate-pulse mb-2" />
                <div className="h-4 bg-(--bg-tertiary) rounded animate-pulse" style={{ animationDelay: `${i * 100}ms` }} />
              </div>
            ))}
          </div>
        );

      case 'diagnostics':
        return (
          <div className="space-y-4">
            <div className="h-32 bg-(--bg-tertiary) rounded-lg animate-pulse" />
            <div className="h-24 bg-(--bg-tertiary) rounded-lg animate-pulse" style={{ animationDelay: '100ms' }} />
            <div className="h-20 bg-(--bg-tertiary) rounded-lg animate-pulse" style={{ animationDelay: '200ms' }} />
          </div>
        );

      default:
        return null;
    }
  };

  return getSkeleton();
};
