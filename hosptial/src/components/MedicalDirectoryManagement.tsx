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
  Activity,
  Layers,
  Stethoscope
} from 'lucide-react';
import { diseaseService, Disease } from '../services/diseaseService';
import { categoryService, DiseaseCategory } from '../services/categoryService';
import { useToast } from '../lib/toast';
import Select from './ui/Select';

interface Props {
  onBack: () => void;
  initialPanelState?: { 
    open: boolean, 
    mode: 'add' | 'edit', 
    disease?: Disease,
    category?: DiseaseCategory 
  };
}

const MedicalDirectoryManagement: React.FC<Props> = ({ onBack, initialPanelState }) => {
  const [activeTab, setActiveTab] = useState<'diseases' | 'categories'>('diseases');
  
  // Disease State
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [uniqueTypes, setUniqueTypes] = useState<string[]>([]);
  const [loadingDiseases, setLoadingDiseases] = useState(true);
  
  // Category State
  const [categories, setCategories] = useState<DiseaseCategory[]>([]);
  const [loadingCategories, setLoadingCategories] = useState(true);

  // Shared UI State
  const [isPanelOpen, setIsPanelOpen] = useState(initialPanelState?.open ?? false);
  const [panelMode, setPanelMode] = useState<'add' | 'edit'>(initialPanelState?.mode ?? 'add');

  useEffect(() => {
    if (initialPanelState?.category) {
      setActiveTab('categories');
    } else if (initialPanelState?.disease) {
      setActiveTab('diseases');
    }
  }, [initialPanelState]);
  const [selectedDisease, setSelectedDisease] = useState<Disease | undefined>(initialPanelState?.disease);
  const [selectedCategory, setSelectedCategory] = useState<DiseaseCategory | undefined>(initialPanelState?.category);
  
  // Controlled category for disease form
  const [activeDiseaseCategory, setActiveDiseaseCategory] = useState<DiseaseCategory | null>(null);

  const [searchQuery, setSearchQuery] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<{ id: string, type: 'disease' | 'category' } | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showToast } = useToast();

  const fetchData = async () => {
    setLoadingDiseases(true);
    setLoadingCategories(true);
    try {
      const [diseaseData, categoryData] = await Promise.all([
        diseaseService.getDiseases(),
        categoryService.getCategories()
      ]);
      setDiseases(diseaseData);
      setCategories(categoryData);
      setUniqueTypes(Array.from(new Set(categoryData.map(c => c.name))));
    } catch (error) {
      showToast('فشل في تحميل البيانات', 'error');
    } finally {
      setLoadingDiseases(false);
      setLoadingCategories(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const filteredDiseases = diseases.filter(d => {
    const query = searchQuery.toLowerCase();
    return d.code.toLowerCase().includes(query) || d.description.toLowerCase().includes(query) || d.disease_type.toLowerCase().includes(query);
  });

  const filteredCategories = categories.filter(c => {
    const query = searchQuery.toLowerCase();
    return c.code.toLowerCase().includes(query) || c.name.toLowerCase().includes(query);
  });

  useEffect(() => {
    if (selectedDisease && categories.length > 0) {
      const cat = categories.find(c => c.name === selectedDisease.disease_type) || null;
      setActiveDiseaseCategory(cat);
    } else {
      setActiveDiseaseCategory(null);
    }
  }, [selectedDisease, categories, isPanelOpen]);

  const handleDelete = async () => {
    if (!showDeleteConfirm) return;
    setIsSubmitting(true);
    try {
      if (showDeleteConfirm.type === 'disease') {
        await diseaseService.deleteDisease(showDeleteConfirm.id);
        setDiseases(prev => prev.filter(d => d.id !== showDeleteConfirm.id));
        showToast('تم حذف رمز المرض بنجاح');
      } else {
        await categoryService.deleteCategory(showDeleteConfirm.id);
        setCategories(prev => prev.filter(c => c.id !== showDeleteConfirm.id));
        showToast('تم حذف التصنيف بنجاح');
      }
      setShowDeleteConfirm(null);
    } catch (err) {
      showToast('حدث خطأ أثناء الحذف', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDiseaseSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      code: formData.get('code') as string,
      description: formData.get('description') as string,
      disease_type: activeDiseaseCategory?.name || '',
    };

    setIsSubmitting(true);
    try {
      const result = await diseaseService.upsertDisease({ 
        ...data, 
        disease_id: selectedDisease?.id || null 
      });
      if (selectedDisease) {
        setDiseases(prev => prev.map(d => d.id === result.id ? result : d));
      } else {
        setDiseases(prev => [result, ...prev]);
      }
      showToast('تم تحديث بيانات المرض بنجاح');
      setIsPanelOpen(false);
    } catch (err) {
      showToast('فشل في حفظ البيانات', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleCategorySave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      code: formData.get('code') as string,
      name: formData.get('name') as string,
    };

    setIsSubmitting(true);
    try {
      const result = await categoryService.upsertCategory({ 
        ...data, 
        id: selectedCategory?.id 
      });
      if (selectedCategory) {
        setCategories(prev => prev.map(c => c.id === result.id ? result : c));
      } else {
        setCategories(prev => [result, ...prev]);
      }
      showToast('تم تحديث بيانات التصنيف بنجاح');
      setIsPanelOpen(false);
    } catch (err) {
      showToast('فشل في حفظ البيانات', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openAdd = () => {
    setSelectedDisease(undefined);
    setSelectedCategory(undefined);
    setPanelMode('add');
    setIsPanelOpen(true);
  };

  const openEditDisease = (disease: Disease) => {
    setSelectedDisease(disease);
    setSelectedCategory(undefined);
    setPanelMode('edit');
    setIsPanelOpen(true);
  };

  const openEditCategory = (cat: DiseaseCategory) => {
    setSelectedCategory(cat);
    setSelectedDisease(undefined);
    setPanelMode('edit');
    setIsPanelOpen(true);
  };

  return (
    <div className="space-y-6 pb-20 relative min-h-full" dir="rtl">
      {/* Header Section */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <nav className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-1">
            <button onClick={onBack} className="hover:text-medical-500 transition-colors">مركز البيانات</button>
            <ChevronRight className="w-3 h-3 rotate-180" />
            <span className="text-[var(--text-primary)]">الدليل الطبي الموحد (ICD-10)</span>
          </nav>
          <h2 className="text-2xl font-display font-bold text-[var(--text-primary)]">
            {activeTab === 'diseases' ? 'إدارة الرموز الطبية' : 'إدارة التصنيفات الطبية'}
          </h2>
        </div>
        
        <div className="flex items-center gap-3">
          <button 
            onClick={openAdd}
            className="flex items-center gap-2 px-6 py-2.5 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 hover:scale-105 active:scale-95 transition-all text-sm whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            <span>إضافة {activeTab === 'diseases' ? 'رمز جديد' : 'تصنيف جديد'}</span>
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex p-1 bg-white dark:bg-white/5 rounded-2xl border border-[var(--border-color)] w-max mx-auto md:mx-0 shadow-sm">
        <button 
          onClick={() => setActiveTab('diseases')}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${activeTab === 'diseases' ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5'}`}
        >
          <Stethoscope className="w-4 h-4" />
          <span>الأمراض</span>
        </button>
        <button 
          onClick={() => setActiveTab('categories')}
          className={`flex items-center gap-2 px-6 py-2.5 rounded-xl text-sm font-bold transition-all ${activeTab === 'categories' ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5'}`}
        >
          <Layers className="w-4 h-4" />
          <span>التصنيفات</span>
        </button>
      </div>

      {/* Large Search Bar - Sticky */}
      <div className="sticky top-0 z-20 bg-[var(--app-bg)] pb-6 pt-2 -mx-4 px-4">
        <div className="relative group shadow-sm transition-all">
          <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-medical-500 transition-colors" />
          <input 
            type="text" 
            placeholder={activeTab === 'diseases' ? "ابحث عن رمز المرض أو الوصف السريري..." : "ابحث عن كود أو اسم التصنيف..."}
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="input-premium py-4 pr-12 pl-6 text-base font-medium min-h-[60px]"
          />
          <div className="absolute left-3 top-1/2 -translate-y-1/2 flex items-center gap-2">
             <span className="text-[10px] font-bold text-slate-400 bg-slate-100 dark:bg-white/5 px-2 py-1 rounded-md uppercase tracking-wider">ICD-10</span>
          </div>
        </div>
      </div>

      {/* List Container */}
      <div className="space-y-3 min-h-[400px]">
        <AnimatePresence mode="popLayout">
          {activeTab === 'diseases' ? (
            loadingDiseases ? (
              [...Array(6)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-white/5 border border-[var(--border-color)] rounded-xl p-4 animate-pulse flex items-center gap-4">
                  <div className="w-20 h-10 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
                  <div className="flex-1 space-y-2">
                    <div className="h-4 w-3/4 bg-slate-100 dark:bg-slate-800 rounded"></div>
                    <div className="h-3 w-1/4 bg-slate-100 dark:bg-slate-800 rounded"></div>
                  </div>
                </div>
              ))
            ) : filteredDiseases.map((disease) => (
              <motion.div
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                key={disease.id}
                className="group card-premium p-4 flex flex-col sm:flex-row sm:items-center gap-4 transition-all hover:border-medical-500 hover:shadow-lg hover:shadow-medical-500/5 group/row"
              >
                <div className="shrink-0">
                  <div className="badge-hollow min-w-[85px] text-center group-hover/row:border-medical-500/30 group-hover/row:text-medical-500 transition-colors">
                    {disease.code}
                  </div>
                </div>
                <div className="flex-1 min-w-0 text-right">
                  <h3 className="text-[var(--text-primary)] font-display font-bold text-base sm:text-lg leading-tight mb-1 truncate">
                    {disease.description}
                  </h3>
                  <div className="flex items-center gap-2 justify-start">
                     <Activity className="w-3.5 h-3.5 text-medical-500" />
                     <span className="text-xs font-medium text-[var(--text-secondary)]">
                       {disease.disease_type}
                     </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:mr-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => openEditDisease(disease)} className="p-2 rounded-lg text-slate-400 hover:bg-medical-500/10 hover:text-medical-600 transition-all"><Edit3 className="w-4 h-4" /></button>
                  <button onClick={() => setShowDeleteConfirm({ id: disease.id, type: 'disease' })} className="p-2 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-500 transition-all"><Trash2 className="w-4 h-4" /></button>
                </div>
              </motion.div>
            ))
          ) : (
            loadingCategories ? (
              [...Array(4)].map((_, i) => (
                <div key={i} className="bg-white dark:bg-white/5 border border-[var(--border-color)] rounded-xl p-4 animate-pulse flex items-center gap-4">
                  <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-xl"></div>
                  <div className="flex-1 h-6 bg-slate-100 dark:bg-slate-800 rounded"></div>
                </div>
              ))
            ) : filteredCategories.map((cat) => (
              <motion.div
                layout
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, scale: 0.95 }}
                key={cat.id}
                className="group card-premium p-4 flex flex-col sm:flex-row sm:items-center gap-4 transition-all hover:border-medical-500 hover:shadow-lg hover:shadow-medical-500/5 group/row"
              >
                <div className="shrink-0">
                  <div className="badge-hollow min-w-[70px] text-center uppercase tracking-wider group-hover/row:border-medical-500/30 group-hover/row:text-medical-500 transition-colors">
                    {cat.code}
                  </div>
                </div>
                <div className="flex-1 min-w-0 text-right">
                  <h3 className="text-[var(--text-primary)] font-display font-bold text-base sm:text-lg leading-tight mb-1 truncate">
                    {cat.name}
                  </h3>
                  <div className="flex items-center gap-2 justify-start mt-1">
                     <span className="badge-faded badge-faded-blue">
                       {cat.count} رمز طبي مرتبط
                     </span>
                  </div>
                </div>
                <div className="flex items-center gap-2 sm:mr-4 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={() => openEditCategory(cat)} className="p-2 rounded-lg text-slate-400 hover:bg-medical-500/10 hover:text-medical-600 transition-all"><Edit3 className="w-4 h-4" /></button>
                  <button onClick={() => setShowDeleteConfirm({ id: cat.id, type: 'category' })} className="p-2 rounded-lg text-slate-400 hover:bg-red-500/10 hover:text-red-500 transition-all"><Trash2 className="w-4 h-4" /></button>
                </div>
              </motion.div>
            ))
          )}
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
                  {panelMode === 'add' ? (activeTab === 'diseases' ? 'إضافة رمز طبي جديد' : 'إضافة تصنيف جديد') : 'تعديل البيانات'}
                </h3>
                <button onClick={() => setIsPanelOpen(false)} className="p-2 hover:bg-slate-100 dark:hover:bg-white/5 rounded-lg"><X className="w-6 h-6 text-slate-500" /></button>
              </div>

              <form 
                onSubmit={activeTab === 'diseases' ? handleDiseaseSave : handleCategorySave} 
                className="space-y-8 flex-1 overflow-y-auto pr-1"
              >
                {activeTab === 'diseases' ? (
                  <div className="space-y-6">
                    <div className="space-y-1">
                       <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">رمز المرض (ICD-10) *</label>
                       <input name="code" defaultValue={selectedDisease?.code} autoFocus type="text" className="input-premium font-mono" placeholder="e.g., J06.9" required dir="ltr" />
                    </div>
                    <div className="space-y-1">
                       <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">الوصف *</label>
                       <textarea name="description" defaultValue={selectedDisease?.description} className="input-premium min-h-[140px] resize-none" placeholder="أدخل الوصف السريري..." required />
                    </div>
                    <div className="space-y-1">
                       <Select 
                        label="التصنيف *"
                        options={categories}
                        value={activeDiseaseCategory}
                        onChange={setActiveDiseaseCategory}
                        placeholder="اختر تصنيف المرض..."
                       />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-6">
                    <div className="space-y-1">
                       <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">كود التصنيف *</label>
                       <input name="code" defaultValue={selectedCategory?.code} autoFocus type="text" className="input-premium font-mono" placeholder="e.g., RESP" required dir="ltr" />
                    </div>
                    <div className="space-y-1">
                       <label className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">اسم التصنيف *</label>
                       <input name="name" defaultValue={selectedCategory?.name} type="text" className="input-premium" placeholder="مثال: أمراض الجهاز التنفسي" required />
                    </div>
                  </div>
                )}

                <div className="mt-auto pt-8 border-t border-[var(--border-color)] flex gap-4">
                  <button type="submit" disabled={isSubmitting} className="flex-1 py-3 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 active:scale-95 transition-all flex items-center justify-center gap-2">
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    <span>{isSubmitting ? 'جاري الحفظ...' : 'حفظ البيانات'}</span>
                  </button>
                  <button type="button" onClick={() => setIsPanelOpen(false)} disabled={isSubmitting} className="flex-1 py-3 bg-slate-100 dark:bg-stone-800 text-slate-500 rounded-xl font-bold transition-colors">إلغاء</button>
                </div>
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirmation */}
      <AnimatePresence>
        {showDeleteConfirm && (
          <>
            <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]" />
            <motion.div initial={{ opacity: 0, scale: 0.9 }} animate={{ opacity: 1, scale: 1 }} exit={{ opacity: 0, scale: 0.9 }} className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-[var(--card-bg)] rounded-3xl p-8 z-[110] shadow-2xl border border-[var(--border-color)] text-center">
              <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center text-red-500 mb-6 mx-auto"><Trash2 className="w-8 h-8" /></div>
              <h3 className="text-xl font-display font-bold mb-2">تأكيد الحذف؟</h3>
              <p className="text-sm text-slate-500 mb-8 font-medium">هل أنت متأكد من رغبتك في حذف هذا {showDeleteConfirm.type === 'disease' ? 'الرمز الطبي' : 'التصنيف'}؟ لا يمكن التراجع عن هذا الإجراء.</p>
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

export default MedicalDirectoryManagement;
