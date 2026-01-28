import React, { useState } from 'react';
import { Copy, Check } from "lucide-react";

interface CitationPanelProps {
  auditId: string;
  bibtex: string;
}

export const CitationPanel: React.FC<CitationPanelProps> = ({ auditId, bibtex }) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(bibtex);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="mt-6 pt-6 border-t border-zinc-200 dark:border-zinc-800">
      <div className="p-4 border border-emerald-500/20 rounded-lg bg-emerald-50/50 dark:bg-emerald-900/10">
        <div className="flex items-center gap-2 mb-2">
          <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
          <span className="text-xs font-mono uppercase tracking-wider text-emerald-700 dark:text-emerald-400">
            Scientific Audit ID: {auditId}
          </span>
        </div>
        
        <p className="text-xs text-zinc-600 dark:text-zinc-400 mb-3 leading-relaxed">
          This analysis was performed using the <b>Deterministic Physics Kernel</b>.
          Include this ID in your publication to ensure reproducibility.
        </p>
        
        <button
          onClick={handleCopy}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium border rounded-md transition-all duration-200 
            border-emerald-200 bg-white text-emerald-700 hover:bg-emerald-50 hover:border-emerald-300
            dark:border-emerald-800 dark:bg-black/20 dark:text-emerald-400 dark:hover:bg-emerald-900/30 dark:hover:border-emerald-700"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? "Copied to Clipboard" : "Copy BibTeX Citation"}
        </button>
      </div>
    </div>
  );
};
