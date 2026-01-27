"use client";

import { useState, useCallback } from "react";
import { getApiUrl } from "../lib/api-config";

interface ExportOptions {
  includeAudit: boolean;
  includeScript: boolean;
  includeRawData: boolean;
  compressionLevel: number;
}

export const useExportIntegrity = (analysisId: string | null) => {
  const [isExporting, setIsExporting] = useState(false);
  const [integrityHash, setIntegrityHash] = useState<string>("");

  const exportWithIntegrity = useCallback(
    async (options: ExportOptions, onProgress?: (progress: number) => void) => {
      if (!analysisId) return { success: false, error: "No analysis selected" };
      
      setIsExporting(true);
      setIntegrityHash("");

      try {
        // Step 1: Fresh calculation (never cached)
        const response = await fetch(getApiUrl(`/api/export/${analysisId}/generate`), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            ...options,
            cacheBuster: Date.now(), // Ensure fresh calculation
            recalculate: true, // Force recalculation
          }),
        });

        if (!response.ok) throw new Error("Export generation failed");

        const reader = response.body?.getReader();
        const contentLength = parseInt(
          response.headers.get("Content-Length") || "0",
        );
        let receivedLength = 0;
        const chunks: Uint8Array[] = [];

        if (reader) {
          while (true) {
            const { done, value } = await reader.read();
            if (done) break;

            chunks.push(value);
            receivedLength += value.length;

            if (onProgress && contentLength > 0) {
              onProgress(Math.round((receivedLength / contentLength) * 100));
            }
          }
        }

        // Combine chunks
        const blob = new Blob(chunks as unknown as BlobPart[], { type: 'application/zip' });

        // Step 2: Calculate integrity hash
        const buffer = await blob.arrayBuffer();
        const hashBuffer = await crypto.subtle.digest("SHA-256", buffer);
        const hashArray = Array.from(new Uint8Array(hashBuffer));
        const hash = hashArray
          .map((b) => b.toString(16).padStart(2, "0"))
          .join("");

        setIntegrityHash(hash);

        // Step 3: Create download with hash in filename
        const url = URL.createObjectURL(blob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `helios_export_${analysisId.slice(0, 8)}_${hash.slice(0, 8)}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);

        URL.revokeObjectURL(url);

        return { success: true, hash };
      } catch (error) {
        console.error("Export failed:", error);
        return {
          success: false,
          error: error instanceof Error ? error.message : "Unknown error",
        };
      } finally {
        setIsExporting(false);
      }
    },
    [analysisId],
  );

  return {
    exportWithIntegrity,
    isExporting,
    integrityHash,
    verifyExport: useCallback(
      async (hash: string) => {
        if (!analysisId) return false;
        // Verify exported file matches hash
        const response = await fetch(getApiUrl(`/api/export/${analysisId}/verify`), {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ hash }),
        });
        return response.ok;
      },
      [analysisId],
    ),
  };
};
