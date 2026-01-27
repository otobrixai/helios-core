"use client";

import React, { useState, useEffect } from "react";
import { Activity, Cpu, MemoryStick, Timer } from "lucide-react";

interface PerformanceMetrics {
  fps: number;
  memory: number;
  renderTime: number;
  dataPoints: number;
  decimationRatio: number;
}

export const PerformanceShield: React.FC<{ visible?: boolean; dataPointCount?: number }> = ({
  visible = false,
  dataPointCount = 0
}) => {
  const [isExpanded, setIsExpanded] = useState(true);
  const [metrics, setMetrics] = useState<PerformanceMetrics>({
    fps: 60,
    memory: 0,
    renderTime: 0,
    dataPoints: dataPointCount,
    decimationRatio: 1,
  });

  const [frameCount, setFrameCount] = useState(0);
  const [lastTime, setLastTime] = useState(0);

  useEffect(() => {
    if (!visible) return;

    // Measure FPS
    let rafId: number;
    const measureFPS = () => {
      const now = performance.now();
      if (lastTime === 0) {
        setLastTime(now);
        rafId = requestAnimationFrame(measureFPS);
        return;
      }

      setFrameCount((prev) => {
        const newCount = prev + 1;
        if (newCount >= 10) {
          const elapsed = now - lastTime;
          const fps = Math.round((newCount * 1000) / elapsed);
          setMetrics((prevMetrics) => ({ ...prevMetrics, fps, dataPoints: dataPointCount }));
          setFrameCount(0);
          setLastTime(now);
        }
        return newCount;
      });

      rafId = requestAnimationFrame(measureFPS);
    };

    // Measure memory (if available)
    const measureMemory = () => {
      if (typeof window !== 'undefined' && "memory" in performance) {
        const memory = (performance as unknown as { memory: { usedJSHeapSize: number } }).memory;
        setMetrics((prevMetrics) => ({
          ...prevMetrics,
          memory: Math.round(memory.usedJSHeapSize / 1024 / 1024),
        }));
      }
    };

    rafId = requestAnimationFrame(measureFPS);
    const memoryInterval = setInterval(measureMemory, 1000);

    return () => {
      cancelAnimationFrame(rafId);
      clearInterval(memoryInterval);
    };
  }, [visible, lastTime, dataPointCount]);

  if (!visible) return null;

  const getPerformanceStatus = () => {
    if (metrics.fps < 30)
      return { color: "text-(--accent-red)", label: "POOR" };
    if (metrics.fps < 50)
      return { color: "text-(--accent-amber)", label: "FAIR" };
    return { color: "text-(--accent-green)", label: "OPTIMAL" };
  };

  const status = getPerformanceStatus();

  return (
    <div className="mt-6 border-t border-(--border-default) pt-6">
      <div className="bg-(--bg-tertiary)/50 rounded-lg p-4 border border-(--border-default)">
        <div 
          className="flex items-center gap-3 mb-4 cursor-pointer select-none"
          onClick={() => setIsExpanded(!isExpanded)}
        >
          <Activity size={18} className={isExpanded ? "text-(--accent-cyan)" : "text-(--text-muted)"} />
          <h3 className="text-[10px] font-bold uppercase tracking-wider flex-1 text-(--text-secondary)">
            System Telemetry
          </h3>
          <div
            className={`text-[9px] px-2 py-0.5 rounded font-bold ${status.color.replace("text-", "bg-")}/20 ${status.color}`}
          >
            {status.label}
          </div>
        </div>

        {isExpanded && (
          <div className="space-y-4 animate-in fade-in slide-in-from-top-1 duration-200">
            <div className="grid grid-cols-2 gap-4">
              <div className="flex items-center gap-2">
                <Cpu size={14} className="text-(--text-muted)" />
                <div>
                  <div className="text-[9px] text-(--text-muted) uppercase">FPS</div>
                  <div className="text-xs font-mono">{metrics.fps}</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <MemoryStick size={14} className="text-(--text-muted)" />
                <div>
                  <div className="text-[9px] text-(--text-muted) uppercase">Memory</div>
                  <div className="text-xs font-mono">{metrics.memory}MB</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <Timer size={14} className="text-(--text-muted)" />
                <div>
                  <div className="text-[9px] text-(--text-muted) uppercase">Latency</div>
                  <div className="text-xs font-mono">{metrics.renderTime}ms</div>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <div className="w-3.5 h-3.5 rounded border border-(--text-muted) flex items-center justify-center">
                   <div className="w-1 h-1 bg-(--text-muted) rounded-full" />
                </div>
                <div>
                  <div className="text-[9px] text-(--text-muted) uppercase">Active Set</div>
                  <div className="text-xs font-mono">{metrics.dataPoints}</div>
                </div>
              </div>
            </div>

            {/* Performance recommendations */}
            {(metrics.fps < 50 || metrics.dataPoints > 1000) && (
              <div className="pt-3 border-t border-(--border-default)">
                <div className="text-[9px] text-(--accent-amber) font-bold uppercase mb-1">
                  Optimizations
                </div>
                <ul className="text-[9px] text-(--text-muted) space-y-1">
                  {metrics.dataPoints > 400 && <li>• Min-Max decimation enabled</li>}
                  {metrics.memory > 500 && <li>• Suggest: Clear analysis cache</li>}
                  <li>• GPU acceleration active</li>
                </ul>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};
