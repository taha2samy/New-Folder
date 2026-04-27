import React, { useEffect, useState, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Terminal, RefreshCcw, PlayCircle, ShieldAlert, Cpu } from 'lucide-react';
import { checkHealth, diagnosticEvents, setForceMock } from '../services/graphqlClient';

export const DiagnosticOverlay: React.FC = () => {
  const [isVisible, setIsVisible] = useState(false);
  const [logs, setLogs] = useState<{ id: string; timestamp: string; type: string; message: string; details?: any }[]>([]);
  const [isForceMocked, setIsForceMocked] = useState(false);
  const logsEndRef = useRef<HTMLDivElement>(null);
  const consecutiveFailures = useRef(0);

  // Auto-scroll logs
  useEffect(() => {
    if (logsEndRef.current) {
      logsEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [logs]);

  useEffect(() => {
    const handleLog = (e: Event) => {
      const customEvent = e as CustomEvent;
      const { type, message, details, timestamp } = customEvent.detail;
      setLogs((prev) => [...prev, { id: Math.random().toString(36).substr(2, 9), timestamp, type, message, details }]);
    };

    diagnosticEvents.addEventListener('log', handleLog);
    return () => diagnosticEvents.removeEventListener('log', handleLog);
  }, []);

  useEffect(() => {
    let pollingInterval: number;

    const performCheck = async () => {
      // Don't check if we explicitly forced mock
      if (isForceMocked) return;

      const result = await checkHealth();
      
      if (result.status === 'unreachable' || result.status === 'not_found' || result.status === 'unauthorized') {
        consecutiveFailures.current += 1;
        
        // Show overlay on first failure
        setIsVisible(true);

        const nextRetry = 5;
        // The checkHealth already logs the error, we just log the retry intent
        diagnosticEvents.dispatchEvent(new CustomEvent('log', {
           detail: {
             type: 'RETRY',
             message: `[RETRY #${consecutiveFailures.current}] Attempting reconnect in ${nextRetry}s...`,
             timestamp: new Date().toISOString().substring(11, 19)
           }
        }));

        pollingInterval = window.setTimeout(performCheck, nextRetry * 1000);
      } else if (result.status === 'online') {
        consecutiveFailures.current = 0;
        setIsVisible(false);
        pollingInterval = window.setTimeout(performCheck, 30000); // 30s background poll when healthy
      } else {
        // mock mode
        setIsVisible(false);
      }
    };

    // Initial check
    if (!isForceMocked) {
      performCheck();
    }

    return () => clearTimeout(pollingInterval);
  }, [isForceMocked]);

  const handleForceMock = () => {
    setIsForceMocked(true);
    setForceMock(true);
    setIsVisible(false);
  };

  const getLogColor = (type: string) => {
    switch (type) {
      case 'ERROR': return 'text-rose-500';
      case 'NETWORK': return 'text-cyan-400';
      case 'SYSTEM': return 'text-purple-400';
      case 'CONFIG': return 'text-amber-400';
      case 'AUTH': return 'text-indigo-400';
      case 'RETRY': return 'text-emerald-400 font-bold';
      case 'MODE': return 'text-fuchsia-400 font-bold';
      case 'CHECK': return 'text-blue-400';
      default: return 'text-emerald-500';
    }
  };

  if (!isVisible && !isForceMocked) return null;

  return (
    <AnimatePresence>
      {isVisible && (
        <motion.div 
          initial={{ opacity: 0, backdropFilter: 'blur(0px)' }}
          animate={{ opacity: 1, backdropFilter: 'blur(12px)' }}
          exit={{ opacity: 0, backdropFilter: 'blur(0px)' }}
          className="fixed inset-0 z-[100] flex flex-col items-center justify-center p-4 bg-slate-900/80 font-sans"
          dir="ltr" // Logs are in English, we force LTR for this diagnostic overlay
        >
          <motion.div 
            initial={{ scale: 0.95, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            className="w-full max-w-4xl bg-[#0F172A] rounded-2xl border-2 border-rose-500/30 shadow-[0_0_50px_rgba(244,63,94,0.15)] overflow-hidden flex flex-col max-h-[85vh]"
          >
            {/* Header */}
            <div className="bg-[#1E293B] px-6 py-4 border-b border-white/5 flex items-center justify-between shrink-0">
               <div className="flex items-center gap-3">
                 <ShieldAlert className="w-6 h-6 text-rose-500 animate-pulse" />
                 <div>
                   <h2 className="text-white font-bold tracking-wider">CONNECTIVITY X-RAY</h2>
                   <p className="text-xs text-rose-400 font-mono">Aggregator Connection Failure Detected</p>
                 </div>
               </div>
               
               <div className="flex items-center gap-2">
                 <Cpu className="w-5 h-5 text-emerald-500" />
                 <span className="text-xs text-emerald-500 font-mono font-bold animate-pulse">AUTO-POLLING ACTIVE</span>
               </div>
            </div>

            {/* Terminal Body */}
            <div className="flex-1 overflow-auto bg-[#0A0F1C] p-6 font-mono text-[13px] leading-relaxed relative">
               <div className="absolute top-0 inset-x-0 h-4 bg-gradient-to-b from-[#0A0F1C] to-transparent z-10 pointer-events-none" />
               <div className="space-y-2 pb-6">
                 {logs.map((log) => (
                   <div key={log.id} className="font-mono">
                     <span className="text-slate-500">[{log.timestamp}]</span>{' '}
                     <span className={`font-bold ${getLogColor(log.type)}`}>
                       [{log.type}]
                     </span>{' '}
                     <span className="text-slate-300">{log.message}</span>
                     {log.details && (
                       <pre className="mt-1 ml-24 p-2 bg-white/5 rounded border border-white/5 text-slate-400 text-xs overflow-x-auto">
                         {JSON.stringify(log.details, null, 2)}
                       </pre>
                     )}
                   </div>
                 ))}
                 <div ref={logsEndRef} />
               </div>
            </div>

            {/* Footer actions */}
            <div className="bg-[#1E293B] p-4 border-t border-white/5 flex items-center justify-end gap-4 shrink-0" dir="rtl">
               <button 
                 onClick={handleForceMock}
                 className="flex items-center gap-2 px-6 py-3 bg-blue-500/10 hover:bg-blue-500/20 text-blue-400 rounded-xl font-bold transition-all border border-blue-500/20 hover:border-blue-500/40"
               >
                 <PlayCircle className="w-5 h-5" />
                 <span className="font-display">التحويل للبيانات التجريبية (Force Mock)</span>
               </button>
            </div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
};
