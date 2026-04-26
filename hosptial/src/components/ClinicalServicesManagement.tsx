import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Plus, 
  Search, 
  X, 
  ChevronRight,
  Trash2,
  Edit3,
  Loader2,
  ListFilter,
  Activity,
  Scissors
} from 'lucide-react';
import { clinicalService, LabExam, SurgicalOperation } from '../services/clinicalService';
import { useToast } from '../lib/toast';
import Select from './ui/Select';

interface Props {
  onBack: () => void;
  initialTab?: 'exams' | 'operations';
}

const ClinicalServicesManagement: React.FC<Props> = ({ onBack, initialTab = 'exams' }) => {
  const [activeTab, setActiveTab] = useState<'exams' | 'operations'>(initialTab);
  
  // Data State
  const [exams, setExams] = useState<LabExam[]>([]);
  const [operations, setOperations] = useState<SurgicalOperation[]>([]);
  const [loading, setLoading] = useState(true);

  // Panel State
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState<'add' | 'edit'>('add');
  const [selectedExam, setSelectedExam] = useState<LabExam | undefined>(undefined);
  const [selectedOperation, setSelectedOperation] = useState<SurgicalOperation | undefined>(undefined);
  
  // UI State
  const [searchQuery, setSearchQuery] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<{ id: string, type: 'exam' | 'operation' } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isMajor, setIsMajor] = useState(false);
  
  // Controlled procedure type for exam form
  const [activeProcedureType, setActiveProcedureType] = useState<{ id: number, name: string } | null>(null);

  const { showToast } = useToast();

  useEffect(() => {
    if (selectedExam) {
      const typeOptions = [
        { id: 1, name: 'نتيجة مفردة (رقم/نص)' },
        { id: 2, name: 'قائمة اختيارات (صح/خطأ)' },
        { id: 3, name: 'تقرير نصي حر' }
      ];
      const type = typeOptions.find(t => t.id === selectedExam.procedure_type) || typeOptions[0];
      setActiveProcedureType(type);
    } else {
      setActiveProcedureType({ id: 1, name: 'نتيجة مفردة (رقم/نص)' });
    }
  }, [selectedExam, isPanelOpen]);

  const fetchData = async () => {
    setLoading(true);
    try {
      const [examData, opData] = await Promise.all([
        clinicalService.getExams(),
        clinicalService.getOperations()
      ]);
      setExams(examData);
      setOperations(opData);
    } catch (error) {
      showToast('فشل في تحميل البيانات', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredExams = exams.filter(e => {
    const query = searchQuery.toLowerCase();
    return e.code.toLowerCase().includes(query) || e.description.toLowerCase().includes(query);
  });

  const filteredOperations = operations.filter(o => {
    const query = searchQuery.toLowerCase();
    return o.code.toLowerCase().includes(query) || o.description.toLowerCase().includes(query);
  });

  const handleDelete = async () => {
    if (!showDeleteConfirm) return;
    setIsSubmitting(true);
    try {
      if (showDeleteConfirm.type === 'exam') {
        await clinicalService.deleteExam(showDeleteConfirm.id);
        setExams(prev => prev.filter(e => e.id !== showDeleteConfirm.id));
        showToast('تم حذف التحليل المخبري بنجاح');
      } else {
        await clinicalService.deleteOperation(showDeleteConfirm.id);
        setOperations(prev => prev.filter(o => o.id !== showDeleteConfirm.id));
        showToast('تم حذف العملية الجراحية بنجاح');
      }
      setShowDeleteConfirm(null);
    } catch (err) {
      showToast('حدث خطأ أثناء الحذف', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleExamSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      code: formData.get('code') as string,
      description: formData.get('description') as string,
      procedure_type: activeProcedureType?.id || 1,
    };

    setIsSubmitting(true);
    try {
      const result = await clinicalService.upsertExam({ 
        ...data, 
        id: selectedExam?.id 
      });
      if (selectedExam) {
        setExams(prev => prev.map(e => e.id === result.id ? result : e));
      } else {
        setExams(prev => [result, ...prev]);
      }
      showToast('تم حفظ بيانات التحليل بنجاح');
      setIsPanelOpen(false);
    } catch (err) {
      showToast('فشل في حفظ البيانات', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleOperationSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      code: formData.get('code') as string,
      description: formData.get('description') as string,
      is_major: isMajor,
    };

    setIsSubmitting(true);
    try {
      const result = await clinicalService.upsertOperation({ 
        ...data, 
        id: selectedOperation?.id 
      });
      if (selectedOperation) {
        setOperations(prev => prev.map(o => o.id === result.id ? result : o));
      } else {
        setOperations(prev => [result, ...prev]);
      }
      showToast('تم حفظ بيانات العملية بنجاح');
      setIsPanelOpen(false);
    } catch (err) {
      showToast('فشل في حفظ البيانات', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openAdd = () => {
    setSelectedExam(undefined);
    setSelectedOperation(undefined);
    setIsMajor(false);
    setPanelMode('add');
    setIsPanelOpen(true);
  };

  const openEditExam = (exam: LabExam) => {
    setSelectedExam(exam);
    setSelectedOperation(undefined);
    setPanelMode('edit');
    setIsPanelOpen(true);
  };

  const openEditOperation = (op: SurgicalOperation) => {
    setSelectedOperation(op);
    setSelectedExam(undefined);
    setIsMajor(op.is_major);
    setPanelMode('edit');
    setIsPanelOpen(true);
  };

  const getProcedureTypeName = (type: number) => {
    switch (type) {
      case 1: return 'نتيجة مفردة (رقم/نص)';
      case 2: return 'قائمة اختيارات (صح/خطأ)';
      case 3: return 'تقرير نصي حر';
      default: return 'غير معروف';
    }
  };

  return (
    <div className="space-y-6 pb-20 relative min-h-full" dir="rtl">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <nav className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-1">
            <button onClick={onBack} className="hover:text-medical-500 transition-colors">مركز البيانات</button>
            <ChevronRight className="w-3 h-3 rotate-180" />
            <span className="text-[var(--text-primary)]">دليل الخدمات الإكلينيكية</span>
          </nav>
          <h2 className="text-2xl font-display font-bold text-[var(--text-primary)]">
            {activeTab === 'exams' ? 'إدارة التحاليل المخبرية' : 'إدارة العمليات الجراحية'}
          </h2>
        </div>
        
        <button 
          onClick={openAdd}
          className="flex items-center gap-2 px-6 py-2.5 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 hover:scale-105 active:scale-95 transition-all text-sm whitespace-nowrap"
        >
          <Plus className="w-4 h-4" />
          <span>إضافة {activeTab === 'exams' ? 'تحليل جديد' : 'عملية جديدة'}</span>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex p-1 bg-white dark:bg-white/5 rounded-2xl border border-[var(--border-color)] w-max mx-auto md:mx-0 shadow-sm">
        <button 
          onClick={() => setActiveTab('exams')}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${activeTab === 'exams' ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5'}`}
        >
          <Activity className="w-4 h-4" />
          <span>التحاليل المخبرية</span>
        </button>
        <button 
          onClick={() => setActiveTab('operations')}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${activeTab === 'operations' ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5'}`}
        >
          <Scissors className="w-4 h-4" />
          <span>العمليات الجراحية</span>
        </button>
      </div>

      {/* Search Bar */}
      <div className="sticky top-0 z-20 bg-[var(--app-bg)] pb-6 pt-2 -mx-4 px-4">
        <div className="relative group shadow-sm transition-all">
          <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-medical-500 transition-colors" />
          <input 
            type="text" 
            placeholder={activeTab === 'exams' ? "ابحث عن كود أو اسم التحليل..." : "ابحث عن كود أو اسم العملية..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-premium py-4 pr-12 pl-6 text-base font-medium min-h-[60px]"
          />
        </div>
      </div>

      {/* List */}
      <div className="space-y-3 min-h-[400px]">
        <AnimatePresence mode="popLayout">
          {loading ? (
             [...Array(5)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-white/5 border border-[var(--border-color)] rounded-xl p-4 animate-pulse flex items-center gap-4">
                   <div className="w-20 h-10 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
                   <div className="flex-1 space-y-2">
                      <div className="h-4 w-3/4 bg-slate-100 dark:bg-slate-800 rounded"></div>
                      <div className="h-3 w-1/4 bg-slate-100 dark:bg-slate-800 rounded"></div>
                   </div>
                </div>
             ))
          ) : (activeTab === 'exams' ? filteredExams : filteredOperations).map((item) => (
            <motion.div
              layout
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, scale: 0.95 }}
              key={item.id}
              className="group card-premium p-4 flex flex-col sm:flex-row sm:items-center gap-4 transition-all hover:border-medical-500 hover:shadow-lg hover:shadow-medical-500/5"
            >
              {/* Code */}
              <div className="shrink-0">
                <div className="badge-hollow min-w-[85px] text-center">
                  {item.code}
                </div>
              </div>

              {/* Content */}
              <div className="flex-1 min-w-0 text-right">
                <h3 className="text-base sm:text-lg font-display font-bold leading-tight mb-1 truncate text-[var(--text-primary)]">
                  {item.description}
                </h3>
                <div className="flex items-center gap-2 justify-start mt-1">
                   {activeTab === 'exams' ? (
                      <span className="text-xs font-medium text-[var(--text-secondary)]">
                        {getProcedureTypeName((item as LabExam).procedure_type)}
                      </span>
                   ) : (
                      <span className={`badge-faded ${(item as SurgicalOperation).is_major ? 'badge-faded-red' : 'badge-faded-emerald'}`}>
                        {(item as SurgicalOperation).is_major ? 'جراحة كبرى' : 'جراحة صغرى'}
                      </span>
                   )}
                </div>
              </div>

              {/* Actions */}
              <div className="flex items-center gap-2 sm:mr-4 opacity-0 group-hover:opacity-100 transition-opacity">
                <button 
                  onClick={() => activeTab === 'exams' ? openEditExam(item as LabExam) : openEditOperation(item as SurgicalOperation)}
                  className="p-2 rounded-lg text-slate-400 hover:bg-medical-500/10 hover:text-medical-600 transition-all font-bold text-xs"
                >
                  <Edit3 className="w-5 h-5" />
                </button>
                <button 
                  onClick={() => setShowDeleteConfirm({ id: item.id, type: activeTab === 'exams' ? 'exam' : 'operation' })}
                  className="p-2 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-500 transition-all font-bold text-xs"
                >
                  <Trash2 className="w-5 h-5" />
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Slide-over Panel */}
      <AnimatePresence>
        {isPanelOpen && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => !isSubmitting && setIsPanelOpen(false)}
              className="fixed inset-0 bg-black/40 backdrop-blur-sm z-[60]"
            />
            <motion.div 
              initial={{ x: '-100%' }}
              animate={{ x: 0 }}
              exit={{ x: '-100%' }}
              transition={{ type: 'spring', damping: 35, stiffness: 350 }}
              className="fixed left-0 top-0 bottom-0 w-full max-w-md bg-[var(--card-bg)]/90 backdrop-blur-xl z-[70] shadow-2xl p-8 flex flex-col border-r border-[var(--border-color)]"
            >
              <div className="flex items-center justify-between mb-10">
                <h3 className="text-2xl font-display font-bold text-[var(--text-primary)]">
                  {panelMode === 'add' ? (activeTab === 'exams' ? 'إضافة تحليل جديد' : 'إضافة عملية جديدة') : 'تعديل البيانات'}
                </h3>
                <button onClick={() => setIsPanelOpen(false)} className="p-2 hover:bg-slate-100 dark:hover:bg-white/5 rounded-lg"><X className="w-6 h-6 text-slate-500" /></button>
              </div>

              <form 
                onSubmit={activeTab === 'exams' ? handleExamSave : handleOperationSave} 
                className="space-y-8 flex-1 overflow-y-auto pr-1"
              >
                <div className="space-y-6">
                  <div className="space-y-1">
                     <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">الكود *</label>
                     <input 
                      name="code" 
                      defaultValue={selectedExam?.code || selectedOperation?.code} 
                      autoFocus 
                      type="text" 
                      className="input-premium font-mono" 
                      placeholder="e.g., CODE-01" 
                      required 
                      dir="ltr" 
                    />
                  </div>

                  <div className="space-y-1">
                     <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">الاسم والوصف *</label>
                     <textarea 
                      name="description" 
                      defaultValue={selectedExam?.description || selectedOperation?.description} 
                      className="input-premium min-h-[140px] resize-none" 
                      placeholder="أدخل الوصف التفصيلي للخدمة..." 
                      required 
                    />
                  </div>

                  {activeTab === 'exams' ? (
                    <div className="space-y-1">
                       <Select 
                        label="طريقة إدخال النتيجة *"
                        options={[
                          { id: 1, name: 'نتيجة مفردة (رقم/نص)' },
                          { id: 2, name: 'قائمة اختيارات (صح/خطأ)' },
                          { id: 3, name: 'تقرير نصي حر' }
                        ]}
                        value={activeProcedureType}
                        onChange={(val: any) => setActiveProcedureType(val)}
                       />
                    </div>
                  ) : (
                    <div className="space-y-3">
                       <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">تصنيف العملية</label>
                       <div className="flex items-center gap-4 bg-slate-100 dark:bg-white/5 p-4 rounded-xl border border-[var(--border-color)]">
                          <button 
                            type="button"
                            onClick={() => setIsMajor(!isMajor)}
                            className={`relative w-12 h-6 rounded-full transition-colors ${isMajor ? 'bg-red-500' : 'bg-slate-300 dark:bg-slate-700'}`}
                          >
                            <motion.div 
                              animate={{ x: isMajor ? 26 : 4 }}
                              className="absolute top-1 left-0 w-4 h-4 bg-white rounded-full shadow-sm"
                            />
                          </button>
                          <span className={`text-sm font-bold ${isMajor ? 'text-red-500' : 'text-medical-500'}`}>
                            {isMajor ? 'جراحة كبرى' : 'جراحة صغرى'}
                          </span>
                       </div>
                    </div>
                  )}
                </div>

                <div className="mt-auto pt-8 border-t border-[var(--border-color)] flex gap-4">
                  <button type="submit" disabled={isSubmitting} className="flex-1 py-3 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 active:scale-95 transition-all flex items-center justify-center gap-2">
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    <span>{isSubmitting ? 'جاري الحفظ...' : 'حفظ البيانات'}</span>
                  </button>
                  <button type="button" onClick={() => setIsPanelOpen(false)} disabled={isSubmitting} className="flex-1 py-3 bg-slate-100 dark:bg-stone-800 text-slate-500 rounded-xl font-bold transition-colors font-display">إلغاء</button>
                </div>
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirm */}
      <AnimatePresence>
        {showDeleteConfirm && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]" />
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-[var(--card-bg)] rounded-3xl p-8 z-[110] shadow-2xl border border-[var(--border-color)] text-center">
              <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center text-red-500 mb-6 mx-auto"><Trash2 className="w-8 h-8" /></div>
              <h3 className="text-xl font-display font-bold mb-2">تأكيد الحذف؟</h3>
              <p className="text-sm text-slate-500 mb-8 font-medium">هل أنت متأكد من رغبتك في حذف هذه الخدمة من الدليل؟ لا يمكن التراجع عن هذا الإجراء.</p>
              <div className="flex gap-4">
                <button disabled={isSubmitting} onClick={handleDelete} className="flex-1 py-3 bg-red-500 text-white rounded-xl font-bold active:scale-95 transition-all">
                  {isSubmitting ? <Loader2 className="w-4 h-4 animate-spin mx-auto" /> : 'حذف'}
                </button>
                <button onClick={() => setShowDeleteConfirm(null)} disabled={isSubmitting} className="flex-1 py-3 bg-slate-100 dark:bg-stone-800 text-slate-500 rounded-xl font-bold transition-colors">تراجع</button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default ClinicalServicesManagement;
