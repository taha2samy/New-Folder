/**
 * @license
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { motion } from 'motion/react';
import { Plus } from 'lucide-react';
import { Layout } from './components/Layout';
import Dashboard from './components/Dashboard';
import MasterDataHub from './components/MasterDataHub';
import { DiagnosticOverlay } from './components/DiagnosticOverlay';
import { ToastProvider } from './lib/toast';

export default function App() {
  const [activeTab, setActiveTab] = useState('overview');
  const [isDarkMode, setIsDarkMode] = useState(false);

  const toggleTheme = () => {
    setIsDarkMode(!isDarkMode);
    if (!isDarkMode) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  };

  const renderContent = () => {
    switch (activeTab) {
      case 'overview':
        return <Dashboard />;
      case 'master-data':
        return <MasterDataHub />;
      case 'patients':
        return (
          <div className="bg-white rounded-2xl border border-slate-200/60 p-12 text-center">
            <h2 className="text-2xl font-display font-bold text-slate-800 mb-4">سجل المرضى</h2>
            <p className="text-slate-500 max-w-md mx-auto">جاري العمل على بناء واجهة سجل المرضى المتقدمة مع فلاتر البحث الذكية.</p>
          </div>
        );
      case 'clinical':
        return (
          <div className="space-y-6">
            <div className="flex items-center justify-between mb-2">
              <div>
                <h2 className="text-2xl font-display font-bold text-[var(--text-primary)]">خريطة الأسرّة التفاعلية</h2>
                <p className="text-[var(--text-secondary)]">متابعة حالة إشغال الأقسام وتوزيع المرضى</p>
              </div>
              <div className="flex gap-4">
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-emerald-500 rounded-sm"></div>
                  <span className="text-xs font-bold">متاح</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-medical-500 rounded-sm"></div>
                  <span className="text-xs font-bold">مشغول</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 bg-amber-500 rounded-sm"></div>
                  <span className="text-xs font-bold">قيد التنظيف</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {['الجناح أ (الجراحة)', 'الجناح ب (الباطنية)', 'العناية المركزة'].map((wing, wingIdx) => (
                <div key={wingIdx} className="card-premium p-6">
                  <h3 className="font-display font-bold text-lg mb-6 border-b border-[var(--border-color)] pb-4">{wing}</h3>
                  <div className="grid grid-cols-5 gap-3">
                    {[...Array(15)].map((_, i) => {
                      const statuses = ['bg-emerald-500', 'bg-medical-500', 'bg-amber-500'];
                      const status = i % 3 === 0 ? statuses[0] : (i % 5 === 0 ? statuses[2] : statuses[1]);
                      return (
                        <motion.div 
                          key={i}
                          whileHover={{ scale: 1.1, zIndex: 20 }}
                          className={`aspect-square ${status} rounded-lg shadow-sm cursor-pointer relative group flex items-center justify-center text-[10px] text-white font-bold font-sans`}
                        >
                          {i + 101}
                          <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-hospital-slate text-white px-2 py-1 rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap text-[10px] z-30">
                             سرير {i + 101}
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                </div>
              ))}
            </div>

            <motion.button 
              whileHover={{ scale: 1.1, rotate: 90 }}
              whileTap={{ scale: 0.9 }}
              animate={{ 
                boxShadow: [
                  "0px 0px 0px 0px rgba(16, 185, 129, 0)",
                  "0px 0px 0px 10px rgba(16, 185, 129, 0.2)",
                  "0px 0px 0px 0px rgba(16, 185, 129, 0)"
                ]
              }}
              transition={{ 
                boxShadow: {
                  duration: 2,
                  repeat: Infinity,
                  ease: "easeInOut"
                }
              }}
              className="fixed bottom-8 left-8 w-16 h-16 bg-emerald-500 text-white rounded-full shadow-2xl flex items-center justify-center hover:scale-110 active:scale-95 transition-all z-50 border-4 border-white dark:border-hospital-slate"
            >
               <Plus className="w-8 h-8" />
            </motion.button>
          </div>
        );
      case 'pharmacy':
        return (
          <div className="bg-white rounded-2xl border border-slate-200/60 p-12 text-center">
            <h2 className="text-2xl font-display font-bold text-slate-800 mb-4">الصيدلية</h2>
            <p className="text-slate-500 max-w-md mx-auto">إدارة المخزون والتنبيهات الذكية للأدوية والمستلزمات.</p>
          </div>
        );
      case 'laboratory':
        return (
          <div className="bg-white rounded-2xl border border-slate-200/60 p-12 text-center">
            <h2 className="text-2xl font-display font-bold text-slate-800 mb-4">المختبر</h2>
            <p className="text-slate-500 max-w-md mx-auto">متابعة طلبات التحاليل والنتائج المخبرية في وقت حقيقي.</p>
          </div>
        );
      case 'billing':
        return (
          <div className="bg-white rounded-2xl border border-slate-200/60 p-12 text-center">
            <h2 className="text-2xl font-display font-bold text-slate-800 mb-4">النظام المالي</h2>
            <p className="text-slate-500 max-w-md mx-auto">إدارة الفواتير، المطالبات التأمينية، والتقارير المالية.</p>
          </div>
        );
      case 'settings':
        return (
          <div className="bg-white rounded-2xl border border-slate-200/60 p-12 text-center">
            <h2 className="text-2xl font-display font-bold text-slate-800 mb-4">الإعدادات</h2>
            <p className="text-slate-500 max-w-md mx-auto">تخصيص النظام وإدارة الصلاحيات والمستخدمين.</p>
          </div>
        );
      default:
        return <Dashboard />;
    }
  };

  return (
    <ToastProvider>
      <DiagnosticOverlay />
      <Layout 
        activeTab={activeTab} 
        setActiveTab={setActiveTab} 
        isDarkMode={isDarkMode} 
        toggleTheme={toggleTheme}
      >
        {renderContent()}
      </Layout>
    </ToastProvider>
  );
}
