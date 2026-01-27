"use client";

import { useState, useEffect, useCallback } from "react";

type Priority = "critical" | "high" | "medium" | "low";

interface PriorityLoadConfig {
  timeoutMs: number;
  deferUntilIdle: boolean;
  placeholder?: React.ReactNode;
}

export const usePriorityLoading = <T>(
  fetchFn: () => Promise<T>,
  priority: Priority,
  config: Partial<PriorityLoadConfig> = {},
) => {
  const [data, setData] = useState<T | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const defaultConfig: PriorityLoadConfig = {
    timeoutMs: priority === "critical" ? 100 : 1000,
    deferUntilIdle: priority === "low",
    placeholder: null,
  };

  const finalConfig = { ...defaultConfig, ...config };

  const loadData = useCallback(async () => {
    setIsLoading(true);
    setError(null);

    try {
      let result: T;

      if (finalConfig.deferUntilIdle && typeof window !== 'undefined' && "requestIdleCallback" in window) {
        // Defer low-priority loads until browser is idle
        result = await new Promise((resolve, reject) => {
          (window as { requestIdleCallback?: (cb: () => void, opts?: { timeout: number }) => void }).requestIdleCallback?.(
            async () => {
              try {
                const data = await fetchFn();
                resolve(data);
              } catch (err) {
                reject(err);
              }
            },
            { timeout: finalConfig.timeoutMs },
          );
        });
      } else {
        // Immediate load for higher priorities
        result = await fetchFn();
      }

      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      console.error(`Priority load (${priority}) failed:`, err);
    } finally {
      setIsLoading(false);
    }
  }, [fetchFn, priority, finalConfig.deferUntilIdle, finalConfig.timeoutMs]);

  useEffect(() => {
    if (priority === "critical") {
      loadData();
    } else {
      // Delay non-critical loads
      const timeout = setTimeout(
        loadData,
        priority === "high" ? 50 : priority === "medium" ? 200 : 500,
      );
      return () => clearTimeout(timeout);
    }
  }, [loadData, priority]);

  return {
    data,
    isLoading,
    error,
    retry: loadData,
    priority,
    config: finalConfig,
  };
};
