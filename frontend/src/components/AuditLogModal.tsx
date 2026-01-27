"use client";

import React from 'react';
import { X, Copy, Terminal } from 'lucide-react';
import { FullDiagnosticReport } from '../types/diagnostics';

interface AuditLogModalProps {
  isOpen: boolean;
  onClose: () => void;
  report: FullDiagnosticReport | null;
}

export const AuditLogModal: React.FC<AuditLogModalProps> = ({ isOpen, onClose, report }) => {
  if (!isOpen) return null;

  const copyToClipboard = () => {
    if (report) {
      navigator.clipboard.writeText(JSON.stringify(report, null, 2));
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-in fade-in duration-200">
      <div className="bg-(--bg-secondary) border border-(--border-default) rounded-2xl w-full max-w-4xl max-h-[85vh] flex flex-col shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        
        {/* Header */}
        <div className="p-6 border-b border-(--border-default) bg-(--bg-tertiary)/50 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-black/40 border border-white/5 text-(--accent-cyan)">
              <Terminal size={20} />
            </div>
            <div>
              <h2 className="text-lg font-black uppercase tracking-widest text-(--text-primary)">
                Scientific Audit Trace
              </h2>
              <p className="text-[10px] text-(--text-muted) uppercase font-bold tracking-tighter mt-0.5">
                Full deterministic provenance log
              </p>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button 
              onClick={copyToClipboard}
              className="p-2 hover:bg-white/5 rounded-lg text-(--text-muted) transition-colors flex items-center gap-2 text-[10px] font-black uppercase tracking-widest"
              title="Copy JSON"
            >
              <Copy size={16} />
              JSON
            </button>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-red-500/20 hover:text-red-400 rounded-lg text-(--text-muted) transition-all"
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-black/20 font-mono text-xs scrollbar-thin scrollbar-thumb-white/10">
          {report ? (
            <pre className="text-(--text-secondary) leading-relaxed">
              {JSON.stringify(report, null, 2)}
            </pre>
          ) : (
            <div className="h-full flex items-center justify-center text-(--text-muted) italic">
              No audit trace available. Run analysis to generate logs.
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="p-4 border-t border-(--border-default) bg-(--bg-tertiary)/30 flex items-center justify-between">
          <div className="flex gap-4">
            <div className="flex items-center gap-1.5">
              <span className="text-[8px] font-black text-(--text-muted) uppercase tracking-widest leading-none">Status:</span>
              <span className={`text-[9px] font-black uppercase ${report?.validation_passed ? 'text-(--accent-green)' : 'text-(--accent-amber)'}`}>
                {report?.validation_passed ? '✓ Validated' : '! Reference Required'}
              </span>
            </div>
            {report?.hash && (
              <div className="flex items-center gap-1.5 border-l border-white/5 pl-4">
                <span className="text-[8px] font-black text-(--text-muted) uppercase tracking-widest leading-none">Hash Code:</span>
                <span className="text-[9px] font-mono text-(--text-muted) opacity-60">
                  {report.hash.substring(0, 16)}...
                </span>
              </div>
            )}
          </div>
          
          <p className="text-[8px] font-black text-(--text-muted) uppercase tracking-[0.2em]">
            Helios Core Audit v1.0
          </p>
        </div>
      </div>
    </div>
  );
};
