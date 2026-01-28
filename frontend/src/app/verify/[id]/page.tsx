"use client";

import React, { useEffect, useState } from 'react';
import { Shield, CheckCircle, Globe, Cpu, Clock, AlertCircle, Download, ExternalLink, Sparkles } from 'lucide-react';
import { useParams } from 'next/navigation';
import Link from 'next/link';
import { QRCodeSVG } from 'qrcode.react';
import QRCode from 'qrcode';
import { getApiUrl } from '@/lib/api-config';

interface VerificationData {
  status: string;
  audit_id: string;
  kernel: string;
  runtime_signature: string;
  verification_statement: string;
  docs: string;
}

export default function VerificationPage() {
  const params = useParams();
  const id = params?.id as string;
  const [data, setData] = useState<VerificationData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [particlePositions] = useState<Array<{left: number, top: number}>>(() => {

    return Array.from({ length: 20 }, () => ({
      left: Math.random() * 100,
      top: Math.random() * 100
    }));
  });

  useEffect(() => {
    if (!id) return;

    fetch(getApiUrl(`verify/${id}`))
      .then(res => {
        if (!res.ok) throw new Error("Verification record not found");
        return res.json();
      })
      .then(setData)
      .catch(err => setError(err.message))
      .finally(() => setLoading(false));
  }, [id]);

  const handlePrint = async () => {
    if (!data) return;
    
    // Create a print-optimized version
    const printWindow = window.open('', '_blank');
    if (!printWindow) return;
    
    const printDate = new Date().toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });

    const verifyUrl = window.location.href;
    const qrCodeDataUrl = await QRCode.toDataURL(verifyUrl, { margin: 1, scale: 4 });

    printWindow.document.write(`
      <!DOCTYPE html>
      <html lang="en">
      <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Helios Core - Verification Certificate</title>
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&display=swap" rel="stylesheet">
        <style>
          @media print {
            @page {
              margin: 0.5in;
              size: A4 portrait;
            }
            
            body {
              -webkit-print-color-adjust: exact !important;
              print-color-adjust: exact !important;
              color-adjust: exact !important;
              margin: 0;
              padding: 0;
              font-family: 'Inter', sans-serif;
              background: white !important;
              color: #111827;
              font-size: 12px;
            }
            
            .print-container {
              max-width: 7in;
              margin: 0 auto;
              padding: 40px;
              border: 4px solid #10b981;
              border-radius: 16px;
              position: relative;
              background: white !important;
              box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
            }
            
            /* Header */
            .print-header {
              display: flex;
              align-items: center;
              justify-content: space-between;
              margin-bottom: 30px;
              padding-bottom: 20px;
              border-bottom: 2px solid #e5e7eb;
            }
            
            .print-logo {
              display: flex;
              align-items: center;
              gap: 12px;
            }
            
            .print-logo-icon {
              background: linear-gradient(135deg, #10b981, #059669);
              color: white;
              padding: 10px;
              border-radius: 50%;
              display: flex;
              align-items: center;
              justify-content: center;
            }
            
            .print-title {
              font-size: 24px;
              font-weight: 900;
              background: linear-gradient(135deg, #10b981, #3b82f6);
              -webkit-background-clip: text;
              background-clip: text;
              color: transparent;
              margin: 0;
            }
            
            .print-cert-id {
              text-align: right;
            }
            
            .print-cert-id-label {
              font-size: 10px;
              color: #6b7280;
              font-weight: 600;
              text-transform: uppercase;
              letter-spacing: 0.1em;
              margin-bottom: 4px;
            }
            
            .print-cert-id-value {
              font-size: 14px;
              font-weight: 700;
              color: #111827;
              font-family: 'Monaco', 'Courier New', monospace;
            }
            
            /* Main Content */
            .print-content {
              display: grid;
              grid-template-columns: 1fr 150px;
              gap: 30px;
              margin-bottom: 30px;
            }
            
            .print-left-column {
              display: flex;
              flex-direction: column;
              gap: 20px;
            }
            
            /* Data Cards */
            .print-data-grid {
              display: grid;
              grid-template-columns: 1fr 1fr;
              gap: 16px;
              margin-bottom: 10px;
            }
            
            .print-data-card {
              padding: 16px;
              border: 1px solid #e5e7eb;
              border-radius: 8px;
              background: #f9fafb;
            }
            
            .print-data-label {
              font-size: 10px;
              color: #6b7280;
              font-weight: 700;
              text-transform: uppercase;
              letter-spacing: 0.1em;
              margin-bottom: 6px;
              display: flex;
              align-items: center;
              gap: 6px;
            }
            
            .print-data-value {
              font-size: 14px;
              font-weight: 600;
              color: #111827;
              word-break: break-word;
            }
            
            /* Signature */
            .print-signature-box {
              padding: 16px;
              background: #f9fafb;
              border: 1px solid #e5e7eb;
              border-radius: 8px;
              margin-bottom: 10px;
            }
            
            .print-signature-label {
              font-size: 10px;
              color: #10b981;
              font-weight: 900;
              text-transform: uppercase;
              letter-spacing: 0.1em;
              margin-bottom: 8px;
            }
            
            .print-signature-value {
              font-family: 'Monaco', 'Courier New', monospace;
              font-size: 10px;
              color: #374151;
              line-height: 1.5;
              word-break: break-all;
              white-space: pre-wrap;
            }
            
            /* Statement */
            .print-statement {
              padding: 20px;
              background: linear-gradient(135deg, #f0fdfa, #ecfdf5);
              border-left: 4px solid #10b981;
              border-radius: 8px;
              font-style: italic;
              color: #065f46;
              font-size: 13px;
              line-height: 1.6;
              margin-bottom: 20px;
            }
            
            /* QR Code Sidebar */
            .print-qr-section {
              display: flex;
              flex-direction: column;
              align-items: center;
              gap: 16px;
            }
            
            .print-qr-code {
              width: 150px;
              height: 150px;
              border: 1px solid #e5e7eb;
              border-radius: 8px;
              padding: 10px;
              background: white;
              display: flex;
              align-items: center;
              justify-content: center;
            }
            
            .print-qr-label {
              font-size: 10px;
              color: #6b7280;
              text-align: center;
              font-weight: 600;
            }
            
            .print-verify-url {
              font-family: 'Monaco', 'Courier New', monospace;
              font-size: 9px;
              color: #374151;
              word-break: break-all;
              text-align: center;
              padding: 8px;
              background: #f9fafb;
              border-radius: 4px;
              border: 1px solid #e5e7eb;
            }
            
            /* Footer */
            .print-footer {
              margin-top: 20px;
              padding-top: 20px;
              border-top: 2px solid #e5e7eb;
              display: grid;
              grid-template-columns: 1fr auto 1fr;
              gap: 30px;
              align-items: center;
            }
            
            .print-footer-left {
              font-size: 10px;
              color: #6b7280;
              line-height: 1.4;
            }
            
            .print-footer-center {
              text-align: center;
            }
            
            .print-footer-right {
              font-size: 10px;
              color: #6b7280;
              line-height: 1.4;
              text-align: right;
            }
            
            .print-watermark {
              position: absolute;
              top: 50%;
              left: 50%;
              transform: translate(-50%, -50%) rotate(-45deg);
              font-size: 80px;
              font-weight: 900;
              color: rgba(16, 185, 129, 0.05);
              pointer-events: none;
              z-index: -1;
            }
            
            /* Hide non-print elements */
            .no-print {
              display: none !important;
            }
            
            /* Force single page */
            .print-container {
              page-break-inside: avoid;
              page-break-after: avoid;
              page-break-before: avoid;
            }
            
            /* Ensure colors print */
            * {
              -webkit-print-color-adjust: exact;
              print-color-adjust: exact;
              color-adjust: exact;
            }
          }
          
          @media screen {
            .print-only {
              display: none !important;
            }
          }
        </style>
      </head>
      <body>
        <div class="print-container">
          <!-- Watermark -->
          <div class="print-watermark">VERIFIED</div>
          
          <!-- Header -->
          <div class="print-header">
            <div class="print-logo">
              <div class="print-logo-icon">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
                </svg>
              </div>
              <h1 class="print-title">Helios Core</h1>
            </div>
            <div class="print-cert-id">
              <div class="print-cert-id-label">Certificate ID</div>
              <div class="print-cert-id-value">${data.audit_id}</div>
            </div>
          </div>
          
          <!-- Main Content -->
          <div class="print-content">
            <div class="print-left-column">
              <!-- Data Grid -->
              <div class="print-data-grid">
                <div class="print-data-card">
                  <div class="print-data-label">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#10b981" stroke-width="2">
                      <circle cx="12" cy="12" r="10"/>
                      <polyline points="12 6 12 12 16 14"/>
                    </svg>
                    Audit ID
                  </div>
                  <div class="print-data-value">${data.audit_id}</div>
                </div>
                
                <div class="print-data-card">
                  <div class="print-data-label">
                    <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="#3b82f6" stroke-width="2">
                      <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
                      <rect x="9" y="9" width="6" height="6"/>
                      <line x1="9" y1="1" x2="9" y2="4"/>
                      <line x1="15" y1="1" x2="15" y2="4"/>
                      <line x1="9" y1="20" x2="9" y2="23"/>
                      <line x1="15" y1="20" x2="15" y2="23"/>
                      <line x1="20" y1="9" x2="23" y2="9"/>
                      <line x1="20" y1="14" x2="23" y2="14"/>
                      <line x1="1" y1="9" x2="4" y2="9"/>
                      <line x1="1" y1="14" x2="4" y2="14"/>
                    </svg>
                    Physics Kernel
                  </div>
                  <div class="print-data-value">${data.kernel}</div>
                </div>
              </div>
              
              <!-- Runtime Signature -->
              <div class="print-signature-box">
                <div class="print-signature-label">Runtime Signature</div>
                <div class="print-signature-value">${data.runtime_signature}</div>
              </div>
              
              <!-- Verification Statement -->
              <div class="print-statement">
                "${data.verification_statement}"
              </div>
            </div>
            
            <!-- QR Code Section -->
            <div class="print-qr-section">
              <div class="print-qr-label">Scan to Verify</div>
              <div class="print-qr-code">
                <img src="${qrCodeDataUrl}" width="130" height="130" alt="QR Code" />
              </div>
              <div class="print-verify-url">${verifyUrl}</div>
            </div>
          </div>
          
          <!-- Footer -->
          <div class="print-footer">
            <div class="print-footer-left">
              <strong>Generated:</strong><br/>
              ${printDate}
            </div>
            
            <div class="print-footer-center">
              <div style="font-size: 9px; color: #6b7280; margin-bottom: 4px;">VERIFICATION SEAL</div>
              <svg width="60" height="60" viewBox="0 0 24 24" fill="#10b981">
                <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
              </svg>
            </div>
            
            <div class="print-footer-right">
              <strong>Global Scientific Registry</strong><br/>
              Helios Core Deterministic Physics<br/>
              Any tampering invalidates this certificate.
            </div>
          </div>
        </div>
        <script>
          window.onload = function() {
            setTimeout(() => {
              window.print();
              setTimeout(() => {
                window.close();
              }, 100);
            }, 100);
          };
        </script>
      </body>
      </html>
    `);
    
    printWindow.document.close();
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-linear-to-br from-gray-950 via-black to-gray-900 flex flex-col items-center justify-center p-6">
        <div className="relative">
          <div className="absolute inset-0 bg-emerald-500/20 blur-xl rounded-full animate-pulse" />
          <div className="relative animate-spin rounded-full h-16 w-16 border-[3px] border-transparent border-t-emerald-500 border-r-emerald-400/50" />
        </div>
        <p className="mt-6 text-emerald-300/80 text-sm font-medium tracking-wider">Validating Audit Trail...</p>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="min-h-screen bg-linear-to-br from-gray-950 via-black to-gray-900 flex items-center justify-center p-8">
        <div className="max-w-md backdrop-blur-sm bg-black/30 border border-red-900/30 rounded-2xl p-8 shadow-2xl">
          <div className="relative mb-6">
            <div className="absolute -inset-4 bg-red-500/10 blur-2xl rounded-full" />
            <div className="relative flex justify-center">
              <div className="p-3 bg-linear-to-br from-red-900 to-red-700 rounded-full">
                <AlertCircle className="w-12 h-12 text-red-300" />
              </div>
            </div>
          </div>
          <h1 className="text-2xl font-bold text-white mb-3 text-center">Invalid Audit ID</h1>
          <p className="text-zinc-400 text-center mb-6 leading-relaxed">
            The verification code provided does not correspond to a valid Helios Core audit trail.
          </p>
          <Link
            href="/"
            className="block w-full py-3 text-center bg-white/5 border border-white/10 rounded-xl hover:bg-white/10 transition-all duration-300 text-white font-medium"
          >
            Return to Helios Core
          </Link>
        </div>
      </div>
    );
  }

  return (
    <>
      {/* Print-only styles */}
      <style jsx global>{`
        @media print {
          body {
            background: white !important;
            color: black !important;
          }
          
          .no-print {
            display: none !important;
          }
          
          * {
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
            color-adjust: exact !important;
          }
        }
      `}</style>
    
      <div className="min-h-screen bg-linear-to-br from-gray-950 via-black to-gray-900 text-white font-sans selection:bg-emerald-500/40 no-print flex flex-col items-center justify-center p-4">
        {/* Enhanced Background Effects */}
        <div className="fixed inset-0 overflow-hidden pointer-events-none">
          <div className="absolute top-[-10%] left-[-10%] w-[40%] h-[40%] bg-emerald-500/10 blur-[120px] rounded-full animate-pulse" />
          <div className="absolute bottom-[-10%] right-[-10%] w-[30%] h-[30%] bg-blue-500/10 blur-[120px] rounded-full" />
          <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[60%] h-[60%] bg-purple-500/5 blur-[100px] rounded-full" />
        </div>

        {/* Floating Particles */}
        <div className="fixed inset-0 pointer-events-none">
          {particlePositions.map((pos, i) => (
            <div
              key={i}
              className="absolute w-px h-px bg-white/5 rounded-full"
              style={{
                left: `${pos.left}%`,
                top: `${pos.top}%`,
                boxShadow: '0 0 20px 2px rgba(16, 185, 129, 0.1)',
              }}
            />
          ))}
        </div>

        <main className="relative z-10 w-full max-w-3xl py-12 md:py-20">
          {/* Validation Seal - Enhanced */}
          <div className="glass-card p-8 md:p-12 border border-white/10 rounded-3xl bg-linear-to-br from-zinc-900/40 via-black/40 to-zinc-900/20 backdrop-blur-2xl shadow-2xl overflow-hidden relative group hover:border-emerald-500/30 transition-all duration-500">
            {/* Animated Glow Borders */}
            <div className="absolute top-0 left-0 w-full h-px bg-linear-to-r from-transparent via-emerald-500 to-transparent opacity-70 group-hover:opacity-100 transition-opacity duration-500" />
            <div className="absolute bottom-0 left-0 w-full h-px bg-linear-to-r from-transparent via-blue-500 to-transparent opacity-30 group-hover:opacity-70 transition-opacity duration-500" />
            <div className="absolute top-0 left-0 w-px h-full bg-linear-to-b from-transparent via-emerald-500 to-transparent opacity-50" />
            <div className="absolute top-0 right-0 w-px h-full bg-linear-to-b from-transparent via-blue-500 to-transparent opacity-30" />
            
            {/* Corner Accents */}
            <div className="absolute -top-2 -left-2 w-4 h-4 border-t-2 border-l-2 border-emerald-500/50 rounded-tl-lg" />
            <div className="absolute -top-2 -right-2 w-4 h-4 border-t-2 border-r-2 border-blue-500/50 rounded-tr-lg" />
            <div className="absolute -bottom-2 -left-2 w-4 h-4 border-b-2 border-l-2 border-emerald-500/30 rounded-bl-lg" />
            <div className="absolute -bottom-2 -right-2 w-4 h-4 border-b-2 border-r-2 border-blue-500/30 rounded-br-lg" />

            <div className="flex flex-col items-center text-center">
              {/* Enhanced Seal Icon */}
              <div className="relative mb-10">
                <div className="absolute inset-0 bg-emerald-500/20 blur-3xl rounded-full scale-150 animate-pulse" />
                <div className="absolute -inset-4 bg-linear-to-r from-emerald-500/20 via-transparent to-blue-500/20 blur-xl rounded-full" />
                <div className="relative bg-linear-to-br from-emerald-600 to-emerald-400 p-5 rounded-full shadow-2xl shadow-emerald-500/30">
                  <div className="relative">
                    <Shield size={56} className="text-white drop-shadow-lg" />
                    <Sparkles className="absolute -top-2 -right-2 w-5 h-5 text-yellow-300 animate-spin" />
                  </div>
                </div>
              </div>

              {/* Header */}
              <div className="relative mb-6">
                <div className="absolute -inset-x-8 -inset-y-4 bg-linear-to-r from-emerald-500/5 via-transparent to-blue-500/5 blur-xl" />
                <h1 className="relative text-4xl md:text-5xl font-black tracking-tighter bg-linear-to-r from-emerald-300 via-white to-blue-300 bg-clip-text text-transparent mb-2 uppercase">
                  Validation Seal
                </h1>
                <div className="flex items-center justify-center gap-3 text-emerald-400 font-mono text-sm tracking-widest">
                  <div className="flex items-center gap-2">
                    <div className="w-2 h-2 bg-emerald-500 rounded-full animate-pulse" />
                    <CheckCircle size={14} className="text-emerald-400" />
                    AUTHENTIC ANALYSIS
                  </div>
                </div>
              </div>

              <div className="w-full h-px bg-linear-to-r from-transparent via-white/10 to-transparent mb-10" />

              {/* Data Grid - Enhanced */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full text-left mb-10">
                <div className="space-y-2 p-4 bg-black/30 rounded-xl border border-white/5 hover:border-emerald-500/20 transition-all duration-300">
                  <div className="text-xs text-zinc-400 uppercase font-bold tracking-widest flex items-center gap-2">
                    <Clock size={14} className="text-emerald-500" />
                    Audit ID
                  </div>
                  <div className="font-mono text-lg text-white bg-black/50 px-3 py-2 rounded-lg border border-white/5 truncate">
                    {data.audit_id}
                  </div>
                </div>
                
                <div className="space-y-2 p-4 bg-black/30 rounded-xl border border-white/5 hover:border-blue-500/20 transition-all duration-300">
                  <div className="text-xs text-zinc-400 uppercase font-bold tracking-widest flex items-center gap-2">
                    <Cpu size={14} className="text-blue-500" />
                    Physics Kernel
                  </div>
                  <div className="text-lg font-bold bg-linear-to-r from-white to-zinc-300 bg-clip-text text-transparent">
                    {data.kernel}
                  </div>
                </div>
              </div>

              {/* Runtime Signature - Enhanced */}
              <div className="w-full bg-linear-to-br from-black/50 to-zinc-900/30 border border-white/5 rounded-2xl p-6 text-left mb-10 backdrop-blur-sm group/signature hover:border-emerald-500/20 transition-all duration-500">
                <div className="flex items-center justify-between mb-4">
                  <div className="text-xs text-emerald-400 uppercase font-black tracking-widest flex items-center gap-2">
                    <div className="w-1.5 h-1.5 bg-emerald-500 rounded-full animate-pulse" />
                    Runtime Signature
                  </div>
                  <div className="text-[10px] text-zinc-600 font-mono">HEX-ENCODED</div>
                </div>
                <div className="relative">
                  <div className="absolute -inset-4 bg-linear-to-r from-emerald-500/5 via-transparent to-blue-500/5 blur-xl opacity-0 group-hover/signature:opacity-100 transition-opacity duration-500" />
                  <div className="flex flex-col md:flex-row gap-6">
                    <div className="flex-1 min-w-0">
                      <p className="relative font-mono text-sm text-zinc-300 leading-relaxed overflow-x-auto whitespace-nowrap py-3 px-4 bg-black/30 rounded-lg border border-white/5 scrollbar-thin scrollbar-thumb-white/10">
                        {data.runtime_signature}
                      </p>
                    </div>
                    {/* QR Code in UI */}
                    <div className="shrink-0 flex items-center justify-center p-2 bg-white rounded-lg border border-emerald-500/20">
                      <QRCodeSVG 
                        value={typeof window !== 'undefined' ? window.location.href : ''} 
                        size={64}
                        level="M"
                        includeMargin={false}
                      />
                    </div>
                  </div>
                </div>
              </div>

              {/* Verification Statement - Enhanced */}
              <div className="relative mb-12 max-w-xl">
                <div className="absolute -left-6 top-1/2 -translate-y-1/2 text-6xl text-emerald-500/20 font-serif">&quot;</div>
                <div className="absolute -right-6 top-1/2 -translate-y-1/2 text-6xl text-emerald-500/20 font-serif">&quot;</div>
                <p className="text-base text-zinc-300 leading-relaxed italic text-center px-8 py-6 bg-linear-to-b from-white/5 to-transparent rounded-2xl border border-white/5">
                  {data.verification_statement}
                </p>
              </div>

              {/* Action Buttons - Enhanced */}
              <div className="flex flex-wrap items-center justify-center gap-5">
                <button 
                  onClick={handlePrint}
                  className="group/btn relative px-8 py-3 bg-linear-to-r from-emerald-600 to-emerald-500 text-white text-sm font-bold uppercase tracking-widest rounded-full hover:shadow-2xl hover:shadow-emerald-500/30 transition-all duration-300 hover:scale-105 min-w-[200px]"
                >
                  <div className="absolute inset-0 bg-linear-to-r from-emerald-400 to-emerald-300 opacity-0 group-hover/btn:opacity-20 blur-xl transition-opacity duration-500" />
                  <div className="relative flex items-center justify-center gap-3">
                    <Download size={16} />
                    Download PDF Certificate
                  </div>
                </button>
                <Link 
                  href="/"
                  className="group/link relative px-8 py-3 border border-white/10 text-white text-sm font-bold uppercase tracking-widest rounded-full hover:bg-linear-to-r hover:from-white/10 hover:to-white/5 transition-all duration-300 min-w-[200px]"
                >
                  <div className="absolute inset-0 border border-white/0 group-hover/link:border-white/10 rounded-full transition-all duration-500" />
                  <div className="relative flex items-center justify-center gap-3">
                    <ExternalLink size={16} />
                    Open Helios Core
                  </div>
                </Link>
              </div>
            </div>
          </div>

          {/* Footer Info - Enhanced */}
          <div className="mt-16 flex flex-col items-center gap-6">
            <div className="inline-flex items-center justify-center gap-3 text-zinc-500 text-xs font-bold uppercase tracking-[0.3em] px-6 py-3 bg-black/20 rounded-full border border-white/5">
              <div className="relative">
                <Globe size={14} className="text-emerald-500/80" />
                <div className="absolute -inset-1 bg-emerald-500/10 blur-sm rounded-full" />
              </div>
              <span className="bg-linear-to-r from-zinc-400 to-zinc-600 bg-clip-text text-transparent">
                Global Scientific Registry Verified
              </span>
            </div>
              <p className="text-xs text-zinc-600 max-w-md uppercase leading-relaxed tracking-wider px-6 py-4 bg-black/10 rounded-xl border border-white/5 text-center">
                Helios Core enforces deterministic solver physics. Any tampering with raw data will result in a mismatched Audit ID.
              </p>
          </div>
        </main>
      </div>
    </>
  );
}