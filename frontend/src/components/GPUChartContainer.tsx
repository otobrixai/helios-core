"use client";

import React, { useRef, useEffect } from "react";

interface GPUChartContainerProps {
  children: React.ReactNode;
  id: string;
  priority?: "high" | "medium" | "low";
}

export const GPUChartContainer: React.FC<GPUChartContainerProps> = ({
  children,
  id,
  priority = "medium",
}) => {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!containerRef.current) return;

    // Force GPU layer for smooth animations
    const container = containerRef.current;
    container.style.transform = "translateZ(0)";
    container.style.backfaceVisibility = "hidden";
    container.style.perspective = "1000px";

    // Apply priority-based optimizations
    if (priority === "high") {
      container.style.willChange = "transform, opacity";
    }

    // Cleanup
    return () => {
      if (container) {
        container.style.willChange = "auto";
      }
    };
  }, [priority]);

  return (
    <div
      ref={containerRef}
      id={`gpu-chart-${id}`}
      className="relative gpu-accelerated overflow-hidden w-full h-full"
      style={{
        // Ensure smooth scrolling within chart
        WebkitOverflowScrolling: "touch",
        // Prevent paint operations during animation
        contain: "content",
        // Optimize for transforms
        isolation: "isolate",
      }}
    >
      {children}

      {/* Performance monitor (dev only) */}
      {process.env.NODE_ENV === "development" && (
        <div className="absolute bottom-2 right-2 opacity-0 hover:opacity-100 transition-opacity z-50">
          <div className="text-[8px] px-2 py-1 bg-black/50 text-white rounded">
            GPU: {priority}
          </div>
        </div>
      )}
    </div>
  );
};
