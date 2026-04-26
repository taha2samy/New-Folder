import React from 'react';
import { motion } from 'motion/react';
import { Activity, Users, Beaker, CreditCard, TrendingUp, AlertCircle, Clock, Plus } from 'lucide-react';

const Dashboard: React.FC = () => {
  const stats = [
    { label: 'إجمالي المنومين', value: '1,284', change: '+12%', trend: 'up', color: 'text-medical-500', bg: 'bg-medical-500/10', icon: Users },
    { label: 'العمليات الجارية', value: '12', secondary: '4 حالات طارئة', color: 'text-red-500', bg: 'bg-red-500/10', icon: Activity },
    { label: 'معدل الإشغال', value: '92%', change: '18 سرير متاح', trend: 'neutral', color: 'text-emerald-500', bg: 'bg-emerald-500/10', icon: AlertCircle },
    { label: 'النتائج المخبرية', value: '48', secondary: 'بانتظار المراجعة', color: 'text-amber-500', bg: 'bg-amber-500/10', icon: Beaker },
  ];

  const recentPatients = [
    { id: '#MED-9201', name: 'أحمد محمود العتيبي', room: 'الغرفة 304', status: 'حرج', statusType: 'urgent' },
    { id: '#MED-8842', name: 'ليلى ناصر العبدالله', room: 'الغرفة 112', status: 'مستقر', statusType: 'stable' },
    { id: '#MED-9104', name: 'خالد محمد القحطاني', room: 'الطوارئ', status: 'جاري الفحص', statusType: 'urgent' },
    { id: '#MED-7731', name: 'مريم يوسف الراشد', room: 'الغرفة 405', status: 'تحسن', statusType: 'stable' },
  ];

  return (
    <div className="space-y-6 pb-20 relative">
      {/* Top Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map((stat, idx) => {
          const Icon = stat.icon;
          return (
            <motion.div 
              key={idx}
              initial={{ opacity: 0, y: 10 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: idx * 0.1 }}
              className="card-premium p-5 flex flex-col justify-between h-36"
            >
              <div className="flex justify-between items-start">
                <span className="text-[13px] font-bold text-slate-500 dark:text-slate-400 font-display">{stat.label}</span>
                <div className={`p-2.5 rounded-xl ${stat.bg} ${stat.color} shadow-sm transition-transform hover:scale-110`}>
                  <Icon className="w-4 h-4" />
                </div>
              </div>
              <div className="mt-2">
                <div className="text-3xl font-bold text-[var(--text-primary)] font-display tracking-tight leading-none mb-2">{stat.value}</div>
                {stat.change && (
                  <span className={`badge-faded ${stat.trend === 'up' ? 'badge-faded-emerald' : 'badge-faded-blue'}`}>
                    {stat.change}
                  </span>
                )}
                {stat.secondary && (
                  <span className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">{stat.secondary}</span>
                )}
              </div>
            </motion.div>
          );
        })}
      </div>

      {/* Bento Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Card 1: Patient Activity Area Chart (Wide) */}
        <div className="lg:col-span-3 card-premium p-6 overflow-hidden flex flex-col min-h-[400px]">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="w-1.5 h-6 bg-medical-500 rounded-full shadow-[0_0_8px_rgba(13,148,136,0.5)]"></div>
              <h3 className="font-display font-bold text-lg">نشاط العيادات والمراجعات</h3>
            </div>
            <div className="flex gap-2">
              {['يومي', 'أسبوعي', 'شهري'].map((t, i) => (
                <button key={i} className={`px-4 py-1.5 rounded-xl text-xs font-bold transition-all ${i === 1 ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'bg-slate-100 dark:bg-white/5 text-slate-500 hover:bg-slate-200 dark:hover:bg-white/10'}`}>
                  {t}
                </button>
              ))}
            </div>
          </div>
          
          <div className="flex-1 relative flex items-end justify-between gap-1 mt-4 px-4 pb-8 overflow-hidden">
             {/* Area Background Gradient */}
             <div className="absolute inset-x-0 bottom-8 h-32 bg-gradient-to-t from-medical-500/5 to-transparent pointer-events-none"></div>
             
             {[30, 45, 25, 70, 50, 85, 65].map((val, i) => (
                <div key={i} className="flex-1 flex flex-col items-center group relative z-10">
                   <div className="w-full flex justify-center mb-1">
                      <motion.div 
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: 0.5 + (i * 0.1) }}
                        className="bg-[var(--card-bg)] border border-[var(--border-color)] px-2 py-1 rounded shadow-sm text-[10px] font-bold opacity-0 group-hover:opacity-100 transition-opacity absolute -top-8"
                      >
                         {val}%
                      </motion.div>
                   </div>
                   
                   <motion.div 
                     initial={{ height: 0 }}
                     animate={{ height: `${val}%` }}
                     transition={{ delay: 0.2 + (i * 0.1), type: 'spring', stiffness: 80 }}
                     className="w-full max-w-[48px] relative"
                   >
                     {/* Bar with gradient end */}
                     <div className="absolute inset-0 bg-gradient-to-t from-medical-500/20 to-medical-500/60 rounded-t-xl group-hover:from-medical-500/40 group-hover:to-medical-500 transition-colors"></div>
                     {/* Top highlight line */}
                     <div className="absolute top-0 inset-x-0 h-1 bg-medical-500 rounded-full shadow-[0_-2px_10px_rgba(13,148,136,0.5)]"></div>
                   </motion.div>
                   
                   <span className="text-[11px] text-slate-400 dark:text-slate-500 mt-4 font-bold font-display">
                    {['حد', 'ن', 'ث', 'ر', 'خ', 'ج', 'س'][i]}
                   </span>
                </div>
             ))}
             
             {/* Decorative Grid Lines */}
             <div className="absolute inset-0 flex flex-col justify-between pointer-events-none opacity-5">
                {[...Array(5)].map((_, i) => <div key={i} className="w-full border-t border-slate-900 dark:border-white"></div>)}
             </div>
          </div>
        </div>

        {/* Card 2: Bed Occupancy Gauge (Square-ish) */}
        <div className="card-premium p-6 flex flex-col items-center justify-center text-center">
          <h3 className="font-display font-bold text-sm text-slate-500 dark:text-slate-400 mb-8 uppercase tracking-wide">إشغال الأسرّة</h3>
          <div className="relative w-40 h-40 flex items-center justify-center mb-8">
             <svg className="w-full h-full -rotate-90">
               <circle cx="80" cy="80" r="70" stroke="currentColor" strokeWidth="14" fill="transparent" className="text-slate-100 dark:text-white/5" />
               <motion.circle 
                 cx="80" cy="80" r="70" 
                 stroke="currentColor" strokeWidth="14" 
                 fill="transparent" 
                 strokeDasharray={439.8}
                 initial={{ strokeDashoffset: 439.8 }}
                 animate={{ strokeDashoffset: 439.8 * (1 - 0.92) }}
                 transition={{ duration: 1.5, ease: "easeOut", delay: 0.5 }}
                 className="text-medical-500 drop-shadow-[0_0_8px_rgba(13,148,136,0.5)]" 
                 strokeLinecap="round"
               />
             </svg>
             <div className="absolute inset-0 flex flex-col items-center justify-center">
               <span className="text-4xl font-bold font-display tracking-tight">92%</span>
               <span className="text-[11px] uppercase tracking-wider text-slate-400 dark:text-slate-500 font-bold font-sans mt-1">مشغول</span>
             </div>
          </div>
          <div className="space-y-1">
            <p className="text-[13px] font-bold text-[var(--text-primary)]">٢٨٩ سرير محجوز</p>
            <p className="text-[11px] text-slate-500 dark:text-slate-400 font-medium">من أصل ٣١٤ سرير متاح حالياً</p>
          </div>
        </div>

        {/* Card 3: Pending Lab Results */}
        <div className="card-premium p-6 flex flex-col min-h-[350px]">
           <div className="flex items-center justify-between mb-6">
              <h3 className="font-display font-bold text-base">بانتظار نتائج المختبر</h3>
              <div className="w-8 h-8 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-500">
                <Clock className="w-4 h-4" />
              </div>
           </div>
           <div className="space-y-3 flex-1 overflow-y-auto pr-1">
              {[
                { title: 'تحليل دم شامل', patient: 'أحمد محمود', time: '١٥ دقيقة', status: 'priority' },
                { title: 'زراعة بكتيرية', patient: 'سارة العلي', time: '١ ساعة', status: 'normal' },
                { title: 'فحص وظائف كلى', patient: 'فهد المطيري', time: '٣ ساعات', status: 'normal' },
              ].map((lab, i) => (
                <motion.div 
                  initial={{ opacity: 0, x: 10 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ delay: 0.6 + (i * 0.1) }}
                  key={i} 
                  className="p-3.5 bg-slate-50 dark:bg-white/5 rounded-xl border-r-4 border-medical-500 transition-all hover:translate-x-1"
                >
                  <div className="flex justify-between items-start mb-1.5">
                    <p className="text-[14px] font-bold text-[var(--text-primary)] leading-none">{lab.title}</p>
                    <span className="text-[10px] text-medical-500 font-bold">{lab.time}</span>
                  </div>
                  <p className="text-[11px] text-[var(--text-secondary)] font-medium">المريض: {lab.patient}</p>
                </motion.div>
              ))}
           </div>
           <button className="w-full py-2.5 mt-6 text-xs font-bold text-medical-600 hover:bg-medical-500/5 rounded-xl transition-all border border-medical-500/20">
             فتح نظام المختبر
           </button>
        </div>

        {/* Card 4: Quick Financial Summary */}
        <div className="lg:col-span-2 card-premium p-7 flex flex-col h-full bg-gradient-to-br from-[var(--card-bg)] to-slate-50 dark:to-white/5">
           <div className="flex items-center justify-between mb-8">
              <h3 className="font-display font-bold text-lg">الموجز المالي اليومي</h3>
              <div className="p-2.5 bg-emerald-500/10 rounded-xl text-emerald-500 shadow-sm transition-transform hover:scale-110">
                <CreditCard className="w-5 h-5" />
              </div>
           </div>
           <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="space-y-2">
                 <p className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wide">العيادات</p>
                 <p className="text-2xl font-bold font-display tracking-tight leading-none">٤٥,٢٩٠</p>
                 <div className="flex items-center gap-1.5 text-[11px] text-emerald-600 font-bold">
                    <TrendingUp className="w-3.5 h-3.5" />
                    <span>+٢٢٪</span>
                 </div>
              </div>
              <div className="space-y-2">
                 <p className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wide">الصيدلية</p>
                 <p className="text-2xl font-bold font-display tracking-tight leading-none">١٢,٨٤٠</p>
                 <p className="text-[11px] text-slate-400 font-bold">مستقر</p>
              </div>
              <div className="space-y-2">
                 <p className="text-xs text-slate-500 dark:text-slate-400 font-bold uppercase tracking-wide">المختبر</p>
                 <p className="text-2xl font-bold font-display tracking-tight leading-none">٨,٤٠٠</p>
                 <p className="text-[11px] text-red-500 font-bold">-٥٪</p>
              </div>
           </div>
           <div className="mt-10 pt-8 border-t border-[var(--border-color)] flex items-end justify-between gap-4">
              <div className="space-y-1">
                 <p className="text-xs text-slate-500 dark:text-slate-400 font-bold">إجمالي المحصل اليوم</p>
                 <div className="flex items-baseline gap-2">
                    <p className="text-4xl font-bold text-emerald-600 font-display tracking-tighter">٦٦,٥٣٠</p>
                    <span className="text-xs font-bold text-slate-400">ر.س</span>
                 </div>
              </div>
              <button className="bg-medical-500 text-white px-8 py-3 rounded-2xl font-bold text-sm shadow-xl shadow-medical-500/30 hover:scale-105 active:scale-95 transition-all">
                 عرض التقارير الكاملة
              </button>
           </div>
        </div>

        {/* Card 5: Recent Patients (Emergency) */}
        <div className="lg:col-span-1 card-premium p-6 flex flex-col h-full overflow-hidden">
           <div className="flex items-center justify-between mb-6">
              <h3 className="font-display font-bold text-lg">الطوارئ (متابعة)</h3>
              <div className="text-[11px] text-medical-600 font-bold cursor-pointer hover:bg-medical-500/5 px-2 py-1 rounded-md transition-colors">عرض الكل</div>
           </div>
           <div className="space-y-2 pr-1 h-[280px] overflow-y-auto custom-scrollbar">
              {recentPatients.map((p, i) => (
                <div key={i} className="flex items-center gap-4 p-3.5 rounded-2xl border border-transparent hover:border-[var(--border-color)] hover:bg-slate-50 dark:hover:bg-white/5 transition-all group cursor-pointer">
                  <div className={`w-3 h-3 rounded-full relative flex-shrink-0 ${p.statusType === 'urgent' ? 'bg-red-500' : 'bg-emerald-500'}`}>
                    {p.statusType === 'urgent' && <div className="absolute inset-0 bg-red-500 rounded-full animate-ping opacity-50"></div>}
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-[14px] font-bold text-[var(--text-primary)] truncate leading-tight">{p.name}</p>
                    <p className="text-[12px] text-[var(--text-secondary)] font-medium">{p.room}</p>
                  </div>
                  <span className={`badge-faded ${p.statusType === 'urgent' ? 'badge-faded-red' : 'badge-faded-emerald'}`}>
                    {p.status}
                  </span>
                </div>
              ))}
           </div>
        </div>
      </div>

      {/* Floating Action Button - Bottom Left for RTL */}
      <motion.button 
        whileHover={{ scale: 1.1, rotate: 90 }}
        whileTap={{ scale: 0.9 }}
        animate={{ 
          boxShadow: [
            "0px 0px 0px 0px rgba(13, 148, 136, 0)",
            "0px 0px 0px 10px rgba(13, 148, 136, 0.2)",
            "0px 0px 0px 0px rgba(13, 148, 136, 0)"
          ]
        }}
        transition={{ 
          boxShadow: {
            duration: 2,
            repeat: Infinity,
            ease: "easeInOut"
          }
        }}
        className="fixed bottom-8 left-8 w-14 h-14 bg-medical-500 text-white rounded-2xl shadow-2xl shadow-medical-500/40 flex items-center justify-center z-50 border-4 border-white dark:border-hospital-slate"
      >
        <Plus className="w-8 h-8" />
      </motion.button>
    </div>
  );
};

export default Dashboard;
