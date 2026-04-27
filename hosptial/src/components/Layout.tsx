import React, { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Search, Bell, Moon, Sun, LayoutDashboard, Users, Stethoscope, Pill, Beaker, CreditCard, Settings, Building2, AlertCircle, CheckCircle2, ShieldAlert } from 'lucide-react';
import { NAV_ITEMS } from '../constants';
import { checkHealth } from '../services/graphqlClient';

interface LayoutProps {
  children: React.ReactNode;
  activeTab: string;
  setActiveTab: (id: string) => void;
  isDarkMode: boolean;
  toggleTheme: () => void;
}

export const Layout: React.FC<LayoutProps> = ({ children, activeTab, setActiveTab, isDarkMode, toggleTheme }) => {
  const [apiStatus, setApiStatus] = useState<{ status: string, message?: string }>({ status: 'connecting' });

  useEffect(() => {
    const fetchStatus = async () => {
      const result = await checkHealth();
      setApiStatus(result);
    };
    
    fetchStatus();
    const interval = setInterval(fetchStatus, 30000); // Check every 30s
    return () => clearInterval(interval);
  }, []);

  const getStatusColor = () => {
    switch (apiStatus.status) {
      case 'online': return 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]';
      case 'mock': return 'bg-blue-500 shadow-[0_0_8px_rgba(59,130,246,0.5)]';
      case 'connecting': return 'bg-amber-500 animate-pulse';
      case 'unauthorized': return 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)] shadow-rose-500/20';
      default: return 'bg-rose-500 shadow-[0_0_8px_rgba(244,63,94,0.5)]';
    }
  };

  const getStatusLabel = () => {
    switch (apiStatus.status) {
      case 'online': return 'متصل بـ Live API';
      case 'mock': return 'بيانات تجريبية (Mock Mode)';
      case 'connecting': return 'جاري التحليل...';
      case 'unauthorized': return apiStatus.message || '🚫 التوكن غير صالح';
      case 'not_found': return apiStatus.message || '⚠️ الرابط غير صحيح (404)';
      default: return apiStatus.message || 'غير قادر على الوصول';
    }
  };

  return (
    <div className="flex h-screen w-full bg-[var(--bg-main)] overflow-hidden font-sans" dir="rtl">
      {/* Right Sidebar - Fixed to Right in RTL */}
      <aside className="w-20 md:w-72 bg-[var(--card-bg)] border-l border-[var(--border-color)] flex flex-col items-center py-8 z-50 fixed right-0 inset-y-0 shadow-2xl transition-all duration-300">
        <div className="mb-12 flex items-center gap-3 px-4 w-full group cursor-pointer">
          <div className="w-10 h-10 bg-medical-500 rounded-xl flex items-center justify-center shadow-[0_0_20px_rgba(13,148,136,0.3)] transition-transform group-hover:rotate-12">
            <Building2 className="w-6 h-6 text-white" />
          </div>
          <span className="hidden md:block font-display font-bold text-xl tracking-tight text-medical-600 dark:text-medical-500">المستشفى</span>
        </div>

        <nav className="flex-1 w-full px-4 space-y-2 relative">
          {NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full flex items-center gap-4 px-4 py-3.5 rounded-xl transition-all duration-300 group relative z-10 ${
                  isActive 
                    ? 'text-white' 
                    : 'text-slate-500 hover:text-medical-600 dark:hover:text-medical-400 hover:bg-medical-500/5'
                }`}
              >
                <Icon className={`w-5 h-5 transition-all duration-300 ${isActive ? 'scale-110 drop-shadow-[0_0_8px_rgba(13,148,136,0.5)]' : 'group-hover:scale-110'}`} />
                <span className="hidden md:block font-medium text-sm font-display">{item.label}</span>
                
                {isActive && (
                  <motion.div
                    layoutId="sidebar-active"
                    className="absolute inset-0 bg-medical-500 rounded-xl -z-10 shadow-[0_0_20px_rgba(13,148,136,0.4)]"
                    transition={{ type: 'spring', stiffness: 400, damping: 33 }}
                  />
                )}
              </button>
            );
          })}
        </nav>

        <div className="mt-auto px-4 w-full space-y-4 pb-4">
          <div className={`px-4 py-3 rounded-xl transition-all duration-500 ${
            apiStatus.status === 'online' 
              ? 'bg-emerald-500/5 border-emerald-500/10' 
              : apiStatus.status === 'connecting'
                ? 'bg-amber-500/5 border-amber-500/10'
                : 'bg-rose-500/5 border-rose-500/10'
          } border`}>
            <div className="flex items-center gap-2 mb-1">
              <div className={`w-2 h-2 rounded-full ${getStatusColor()}`}></div>
              <span className="text-[10px] font-bold text-slate-500 uppercase tracking-wider">حالة البيانات</span>
            </div>
            <p className={`text-[10px] font-bold leading-relaxed ${
              apiStatus.status === 'online' ? 'text-emerald-600 dark:text-emerald-500' :
              apiStatus.status === 'connecting' ? 'text-amber-600 dark:text-amber-500' :
              'text-rose-600 dark:text-rose-500'
            }`}>
              {getStatusLabel()}
            </p>
          </div>
          
          <button className="w-full flex items-center gap-4 px-4 py-3 rounded-xl text-slate-500 hover:text-medical-500 transition-all group">
            <Settings className="w-5 h-5 group-hover:rotate-45 transition-transform duration-500" />
            <span className="hidden md:block font-medium text-sm font-display">الدعم الفني</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area - Shifted Left to clear Right Sidebar */}
      {/* ms (margin-inline-start) is MARGIN-RIGHT in RTL */}
      <main className="flex-1 flex flex-col min-w-0 relative h-screen ms-20 md:ms-72 transition-all duration-300 bg-[var(--bg-main)]">
        {/* Header */}
        <header className="h-16 glass sticky top-0 z-40 flex items-center justify-between px-6 border-b border-[var(--border-color)]">
          {/* Page Title (Right side in RTL) */}
          <div className="flex items-center gap-4 flex-shrink-0">
             <h1 className="font-display font-bold text-lg text-[var(--text-primary)]">
              {NAV_ITEMS.find(i => i.id === activeTab)?.label}
             </h1>
          </div>

          {/* Command Search */}
          <div className="flex flex-1 justify-start ml-8 font-sans">
            <motion.div 
              className="w-full max-w-2xl relative group"
              whileFocus={{ scale: 1.01 }}
              transition={{ type: 'spring', stiffness: 300, damping: 20 }}
            >
              <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-medical-500 transition-colors" />
              <input 
                type="text" 
                placeholder="ابحث عن ملف طبي، مريض، أو موعد..."
                className="input-premium pr-11 shadow-sm"
              />
              <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-1 opacity-50 group-focus-within:opacity-100 transition-opacity">
                <kbd className="px-1.5 py-0.5 rounded border border-[var(--border-color)] text-[9px] text-slate-500 bg-[var(--card-bg)] font-sans">Ctrl</kbd>
                <kbd className="px-1.5 py-0.5 rounded border border-[var(--border-color)] text-[9px] text-slate-500 bg-[var(--card-bg)] font-sans uppercase">K</kbd>
              </div>
            </motion.div>
          </div>

          {/* User Profile & Theme Toggle (Left side in RTL) */}
          <div className="flex items-center gap-4 flex-shrink-0">
            <button 
              onClick={toggleTheme}
              className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-all text-slate-600 dark:text-slate-400"
            >
              {isDarkMode ? <Sun className="w-5 h-5 text-amber-400" /> : <Moon className="w-5 h-5" />}
            </button>
            <button className="p-2.5 rounded-xl hover:bg-slate-100 dark:hover:bg-slate-800 transition-colors relative">
              <Bell className="w-5 h-5 text-slate-600 dark:text-slate-400" />
              <span className="absolute top-2.5 right-2.5 w-2 h-2 bg-red-500 rounded-full border-2 border-[var(--card-bg)]"></span>
            </button>
            <div className="flex items-center gap-3 ps-4 border-s border-[var(--border-color)]">
              <div className="text-right hidden sm:block">
                <p className="text-sm font-bold text-[var(--text-primary)] leading-none">د. أحمد خالد</p>
                <p className="text-xs text-[var(--text-secondary)] mt-1 font-medium italic opacity-75">كبير الأطباء</p>
              </div>
              <div className="w-10 h-10 rounded-full bg-slate-200 dark:bg-slate-800 flex items-center justify-center overflow-hidden border-2 border-white dark:border-slate-800 shadow-sm">
                <img 
                  src="https://images.unsplash.com/photo-1612349317150-e413f6a5b16d?q=80&w=2070&auto=format&fit=crop" 
                  alt="Avatar" 
                  className="w-full h-full object-cover"
                />
              </div>
            </div>
          </div>
        </header>

        {/* Dynamic Content */}
        <section className="flex-1 overflow-y-auto p-6 relative scroll-smooth overflow-x-hidden bg-[var(--bg-main)]">
           <AnimatePresence mode="wait">
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -20 }}
              transition={{ duration: 0.3, ease: [0.23, 1, 0.32, 1] }}
              className="h-full w-full max-w-full"
            >
              {children}
            </motion.div>
          </AnimatePresence>
        </section>
      </main>
    </div>
  );
};
