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
  Bed as BedIcon,
  CheckCircle2,
  AlertCircle,
  RefreshCw,
  Hammer,
  CreditCard,
  Building2,
  Filter,
  ArrowLeft,
  DollarSign
} from 'lucide-react';
import { facilityService, Ward, Bed, BedStatus, BedCategory } from '../services/facilityService';
import { useToast } from '../lib/toast';
import Select from './ui/Select';
import CustomCombobox from './ui/Combobox';

interface Props {
  onBack: () => void;
}

const FacilityManagement: React.FC<Props> = ({ onBack }) => {
  const [activeTab, setActiveTab] = useState<'wards' | 'categories' | 'beds'>('wards');
  
  // Data State
  const [wards, setWards] = useState<Ward[]>([]);
  const [categories, setCategories] = useState<BedCategory[]>([]);
  const [beds, setBeds] = useState<Bed[]>([]);
  const [loading, setLoading] = useState(true);

  // Panel State
  const [isPanelOpen, setIsPanelOpen] = useState(false);
  const [panelMode, setPanelMode] = useState<'add' | 'edit'>('add');
  const [editingItem, setEditingItem] = useState<any>(null);

  // Form selections for controlled custom components
  const [selectedWard, setSelectedWard] = useState<Ward | null>(null);
  const [selectedCategory, setSelectedCategory] = useState<BedCategory | null>(null);
  const [selectedStatus, setSelectedStatus] = useState<{ id: BedStatus, name: string } | null>(null);

  // UI State
  const [searchQuery, setSearchQuery] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showToast } = useToast();

  const fetchData = async () => {
    setLoading(true);
    try {
      const [wData, cData, bData] = await Promise.all([
        facilityService.getWards(),
        facilityService.getCategories(),
        facilityService.getBeds()
      ]);
      setWards(wData);
      setCategories(cData);
      setBeds(bData);
    } catch (err) {
      showToast('فشل في تحميل البيانات', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (editingItem && activeTab === 'beds') {
      const ward = wards.find(w => w.id === editingItem.ward_id) || null;
      const category = categories.find(c => c.id === editingItem.category_id) || null;
      setSelectedWard(ward);
      setSelectedCategory(category);
      
      const statusOptions = [
        { id: 'AVAILABLE', name: 'متاح للاستخدام' },
        { id: 'OCCUPIED', name: 'مشغول حالياً' },
        { id: 'CLEANING', name: 'جاري التعقيم' },
        { id: 'MAINTENANCE', name: 'تحت الصيانة' }
      ] as const;
      const status = statusOptions.find(s => s.id === editingItem.status) || statusOptions[0];
      setSelectedStatus(status);
    } else {
      setSelectedWard(null);
      setSelectedCategory(null);
      setSelectedStatus({ id: 'AVAILABLE', name: 'متاح للاستخدام' });
    }
  }, [editingItem, activeTab, wards, categories]);

  const handleSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setIsSubmitting(true);
    const formData = new FormData(e.currentTarget);
    
    try {
      if (activeTab === 'wards') {
        const data = {
          name: formData.get('name') as string,
          code: formData.get('code') as string,
          is_opd: formData.get('is_opd') === 'on',
        };
        await facilityService.upsertWard({ ...data, id: editingItem?.id });
        showToast(editingItem ? 'تم تحديث بيانات العنبر' : 'تم إضافة العنبر بنجاح');
      } else if (activeTab === 'categories') {
        const data = {
          name: formData.get('name') as string,
          description: formData.get('description') as string,
          price: parseFloat(formData.get('price') as string),
        };
        await facilityService.upsertCategory({ ...data, id: editingItem?.id });
        showToast(editingItem ? 'تم تحديث الفئة والسعر' : 'تم إضافة الفئة بنجاح');
      } else if (activeTab === 'beds') {
        const data = {
          code: formData.get('code') as string,
          ward_id: selectedWard?.id || '',
          category_id: selectedCategory?.id || '',
          status: selectedStatus?.id || 'AVAILABLE',
        };
        await facilityService.upsertBed({ ...data, id: editingItem?.id });
        showToast(editingItem ? 'تم تحديث بيانات السرير' : 'تم تسجيل السرير بنجاح');
      }
      
      setIsPanelOpen(false);
      fetchData();
    } catch (err) {
      showToast('خطأ في حفظ البيانات', 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = async (id: string) => {
    if (!confirm('هل أنت متأكد من الحذف؟')) return;
    try {
      if (activeTab === 'wards') await facilityService.deleteWard(id);
      else if (activeTab === 'categories') await facilityService.deleteCategory(id);
      else if (activeTab === 'beds') await facilityService.deleteBed(id);
      
      showToast('تم الحذف بنجاح');
      fetchData();
    } catch (err) {
      showToast('فشل في الحذف', 'error');
    }
  };

  const getStatusColor = (status: BedStatus) => {
    switch (status) {
      case 'AVAILABLE': return 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20';
      case 'OCCUPIED': return 'bg-rose-500/10 text-rose-600 dark:text-rose-400 border-rose-500/20';
      case 'CLEANING': return 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20';
      case 'MAINTENANCE': return 'bg-slate-500/10 text-slate-600 dark:text-slate-400 border-slate-500/20';
      default: return 'bg-slate-100 text-slate-500';
    }
  };

  const filteredItems = () => {
    if (activeTab === 'wards') return wards.filter(w => w.name.includes(searchQuery) || w.code.includes(searchQuery));
    if (activeTab === 'categories') return categories.filter(c => c.name.includes(searchQuery));
    if (activeTab === 'beds') return beds.filter(b => b.code.includes(searchQuery));
    return [];
  };

  return (
    <div className="w-full flex flex-col min-h-screen bg-[var(--app-bg)] transition-colors duration-300" dir="rtl">
      {/* Header Area */}
      <div className="w-full bg-[var(--app-bg)] px-8 py-6 sticky top-0 z-40">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="flex flex-col gap-1">
            <nav className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-1">
              <button 
                onClick={onBack}
                className="hover:text-medical-500 transition-colors"
              >
                مركز البيانات
              </button>
              <ChevronRight className="w-3 h-3 rotate-180" />
              <span className="text-[var(--text-primary)]">إدارة المنشآت والأسرة</span>
            </nav>
            <h1 className="text-2xl font-display font-bold text-[var(--text-primary)]">
              {activeTab === 'wards' ? 'أجنحة وعنابر التنويم' : activeTab === 'categories' ? 'فئات الإقامة والتسعير' : 'سجل الأسرة الفندقية'}
            </h1>
          </div>

          <button 
            onClick={() => { setEditingItem(null); setPanelMode('add'); setIsPanelOpen(true); }}
            className="flex items-center gap-2 px-6 py-2.5 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 hover:scale-105 active:scale-95 transition-all text-sm whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            <span>إضافة {activeTab === 'wards' ? 'عنبر' : activeTab === 'categories' ? 'فئة' : 'سرير'}</span>
          </button>
        </div>

        {/* Tab Navigation (Segmented Control) */}
        <div className="flex p-1 bg-white dark:bg-white/5 rounded-2xl border border-[var(--border-color)] w-max mt-6 shadow-sm">
          <button 
            onClick={() => setActiveTab('wards')}
            className={`px-6 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === 'wards' ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5'}`}
          >عنابر التنويم</button>
          <button 
            onClick={() => setActiveTab('categories')}
            className={`px-6 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === 'categories' ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5'}`}
          >فئات الإقامة</button>
          <button 
            onClick={() => setActiveTab('beds')}
            className={`px-6 py-2 rounded-xl text-sm font-bold transition-all ${activeTab === 'beds' ? 'bg-medical-500 text-white shadow-lg shadow-medical-500/20' : 'text-slate-500 hover:bg-slate-50 dark:hover:bg-white/5'}`}
          >سجل الأسرة</button>
        </div>
      </div>

      <main className="flex-1 px-8 py-2 w-full overflow-x-hidden">
        {/* Search & Filter */}
        <div className="flex items-center gap-4 mb-8">
          <div className="relative flex-1 group">
            <Search className="absolute right-4 top-1/2 -translate-y-1/2 w-5 h-5 text-slate-400 group-focus-within:text-medical-500 transition-colors" />
            <input 
              type="text" 
              placeholder={`بحث سريع في ${activeTab === 'wards' ? 'العنابر' : activeTab === 'categories' ? 'الفئات' : 'الأكواد'}...`}
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full h-12 pr-12 pl-6 bg-white dark:bg-white/5 border border-[var(--border-color)] rounded-xl font-bold focus:border-medical-500 focus:outline-none transition-all text-[var(--text-primary)] text-sm"
            />
          </div>
          <button className="h-12 w-12 flex items-center justify-center bg-white dark:bg-white/5 border border-[var(--border-color)] rounded-xl text-slate-400 hover:text-medical-500 transition-all shadow-sm">
            <Filter className="w-5 h-5" />
          </button>
        </div>

        {/* Content Area */}
        <AnimatePresence mode="wait">
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-4">
              <Loader2 className="w-10 h-10 animate-spin text-medical-500" />
              <span className="font-bold text-slate-400">جاري تحميل البيانات...</span>
            </div>
          ) : (
            <motion.div
              key={activeTab}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              exit={{ opacity: 0, x: -20 }}
              className="grid grid-cols-1 gap-4"
            >
              {activeTab === 'wards' && (
                <div className="space-y-3">
                  {filteredItems().map((ward: Ward) => (
                    <div key={ward.id} className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-5 flex flex-col md:flex-row md:items-center justify-between gap-6 group hover:border-medical-500 transition-all shadow-sm">
                      <div className="flex items-center gap-5">
                        <div className="w-12 h-12 bg-slate-50 dark:bg-white/5 rounded-xl flex items-center justify-center text-slate-400 border border-[var(--border-color)]">
                           <Building2 className="w-6 h-6" />
                        </div>
                        <div>
                          <h3 className="text-lg font-display font-bold text-[var(--text-primary)]">{ward.name}</h3>
                          <div className="flex items-center gap-3 mt-1">
                            <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-slate-100 dark:bg-white/10 text-slate-500 dark:text-slate-400 border border-[var(--border-color)] uppercase tracking-wider">{ward.code}</span>
                            <span className={`text-[10px] font-black uppercase px-2 py-0.5 rounded ${ward.is_opd ? 'bg-blue-500/10 text-blue-600 dark:text-blue-400' : 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'}`}>
                              {ward.is_opd ? 'Clinics' : 'In-Patient'}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="flex items-center gap-8 me-4">
                        <div className="text-left">
                           <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest text-right">السعة المتاحة</p>
                           <p className="text-xl font-display font-bold text-medical-600 dark:text-medical-400">{ward.beds_count} سرير</p>
                        </div>
                        <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-all">
                          <button 
                            onClick={() => { setEditingItem(ward); setPanelMode('edit'); setIsPanelOpen(true); }}
                            className="p-2.5 bg-slate-50 dark:bg-white/5 text-slate-400 hover:text-medical-600 rounded-lg border border-[var(--border-color)] transition-all"
                          ><Edit3 className="w-4 h-4" /></button>
                          <button 
                            onClick={() => handleDelete(ward.id)}
                            className="p-2.5 bg-slate-50 dark:bg-white/5 text-slate-400 hover:text-rose-600 rounded-lg border border-[var(--border-color)] transition-all"
                          ><Trash2 className="w-4 h-4" /></button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'categories' && (
                <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-6">
                  {filteredItems().map((cat: BedCategory) => (
                    <div key={cat.id} className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-6 flex flex-col gap-6 group hover:border-medical-500 transition-all shadow-sm relative overflow-hidden">
                      <div className="flex justify-between items-start">
                        <div className="w-12 h-12 bg-medical-500/10 text-medical-600 dark:text-medical-400 rounded-xl flex items-center justify-center border border-medical-500/10">
                           <CreditCard className="w-6 h-6" />
                        </div>
                        <div className="flex items-center gap-1 opacity-100 md:opacity-0 group-hover:opacity-100 transition-all">
                          <button 
                            onClick={() => { setEditingItem(cat); setPanelMode('edit'); setIsPanelOpen(true); }}
                            className="p-2 text-slate-400 hover:text-medical-600 transition-colors"
                          ><Edit3 className="w-4 h-4" /></button>
                          <button 
                            onClick={() => handleDelete(cat.id)}
                            className="p-2 text-slate-400 hover:text-rose-600 transition-colors"
                          ><Trash2 className="w-4 h-4" /></button>
                        </div>
                      </div>

                      <div>
                        <h3 className="text-lg font-display font-bold text-[var(--text-primary)] mb-1">{cat.name}</h3>
                        <p className="text-xs text-[var(--text-secondary)] leading-relaxed line-clamp-2">{cat.description}</p>
                      </div>

                      <div className="mt-2 pt-5 border-t border-[var(--border-color)] flex items-center justify-between">
                         <div className="flex items-center gap-1.5">
                           <span className="text-2xl font-display font-bold text-medical-600 dark:text-medical-400">{cat.price.toLocaleString()}</span>
                           <span className="text-[10px] font-bold text-slate-400 font-sans">ريال / يوم</span>
                         </div>
                         <div className="px-3 py-1 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold rounded-lg border border-emerald-500/10">
                           الفئة النشطة
                         </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}

              {activeTab === 'beds' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 2xl:grid-cols-5 gap-6">
                  {filteredItems().map((bed: Bed) => {
                    const ward = wards.find(w => w.id === bed.ward_id);
                    const category = categories.find(c => c.id === bed.category_id);
                    
                    return (
                      <div key={bed.id} className="bg-[var(--card-bg)] border border-[var(--border-color)] rounded-2xl p-5 flex flex-col gap-5 hover:shadow-xl hover:shadow-medical-500/5 transition-all group relative overflow-hidden">
                        <div className="flex justify-between items-start">
                          <div className={`p-2.5 rounded-xl border ${getStatusColor(bed.status)}`}>
                             <BedIcon className="w-5 h-5" />
                          </div>
                          <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-all">
                            <button onClick={() => { setEditingItem(bed); setPanelMode('edit'); setIsPanelOpen(true); }} className="p-2 text-slate-400 hover:text-medical-600"><Edit3 className="w-4 h-4" /></button>
                            <button onClick={() => handleDelete(bed.id)} className="p-2 text-slate-400 hover:text-rose-600"><Trash2 className="w-4 h-4" /></button>
                          </div>
                        </div>

                        <div>
                          <p className="text-[9px] font-black text-slate-400 uppercase tracking-widest mb-1">{category?.name || 'فئة غير محددة'}</p>
                          <h3 className="text-xl font-mono font-bold text-[var(--text-primary)]">{bed.code}</h3>
                        </div>

                        <div className="space-y-3">
                           <div className="flex items-center gap-2 text-[10px] font-bold text-[var(--text-secondary)]">
                              <Building2 className="w-3.5 h-3.5" />
                              <span className="truncate">{ward?.name || 'بدون جناح'}</span>
                           </div>
                           <div className={`flex items-center gap-2 text-[10px] font-bold px-3 py-1.5 rounded-lg border w-full ${getStatusColor(bed.status)} lg:w-fit`}>
                             {bed.status === 'AVAILABLE' && <CheckCircle2 className="w-3.5 h-3.5" />}
                             {bed.status === 'OCCUPIED' && <AlertCircle className="w-3.5 h-3.5" />}
                             {bed.status === 'CLEANING' && <RefreshCw className="w-3.5 h-3.5 animate-spin" />}
                             {bed.status === 'MAINTENANCE' && <Hammer className="w-3.5 h-3.5" />}
                             <span>
                               {bed.status === 'AVAILABLE' ? 'متاح للاستخدام' : 
                                bed.status === 'OCCUPIED' ? 'مشغول حالياً' : 
                                bed.status === 'CLEANING' ? 'جاري التعقيم' : 'تحت الصيانة'}
                             </span>
                           </div>
                        </div>
                        
                        {bed.patient_name && (
                          <div className="mt-1 pt-4 border-t border-[var(--border-color)]">
                             <p className="text-[9px] font-black text-slate-400 uppercase tracking-wider mb-1">المريض المحجوز:</p>
                             <p className="text-sm font-bold text-[var(--text-primary)] truncate">{bed.patient_name}</p>
                          </div>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </motion.div>
          )}
        </AnimatePresence>
      </main>

      {/* Slide-over Form Panel */}
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
              initial={{ x: '100%' }}
              animate={{ x: 0 }}
              exit={{ x: '100%' }}
              transition={{ type: 'spring', damping: 35, stiffness: 350 }}
              className="fixed left-0 top-0 bottom-0 w-full max-w-md bg-[var(--card-bg)]/90 backdrop-blur-xl z-[70] shadow-2xl p-8 flex flex-col border-r border-[var(--border-color)]"
            >
               <div className="flex items-center justify-between mb-10">
                 <div>
                   <h3 className="text-2xl font-display font-bold text-[var(--text-primary)]">
                     {panelMode === 'add' ? 'إضافة سجل جديد' : 'تحديث البيانات'}
                   </h3>
                   <p className="text-xs text-slate-400 font-bold mt-1">
                     {activeTab === 'wards' ? 'إدارة الأجنحة والأقسام' : activeTab === 'categories' ? 'تعديل الفئات السعرية' : 'تسجيل سرير جديد'}
                   </p>
                 </div>
                 <button onClick={() => setIsPanelOpen(false)} className="p-2 hover:bg-slate-100 dark:hover:bg-white/5 rounded-lg transition-colors">
                   <X className="w-6 h-6 text-slate-400" />
                 </button>
               </div>

               <form onSubmit={handleSave} className="flex-1 space-y-6 overflow-y-auto pr-1">
                 {activeTab === 'wards' && (
                   <>
                     <div className="space-y-1">
                        <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">اسم القسم / الجناح *</label>
                        <input name="name" defaultValue={editingItem?.name} required placeholder="مثال: جناح الجراحة" className="input-premium" />
                     </div>
                     <div className="space-y-1">
                        <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">كود التمييز *</label>
                        <input name="code" defaultValue={editingItem?.code} required placeholder="W-SURG" className="input-premium font-mono" />
                     </div>
                     <div className="flex items-center gap-4 p-4 bg-slate-50 dark:bg-white/2 rounded-xl border border-[var(--border-color)]">
                        <input type="checkbox" name="is_opd" defaultChecked={editingItem?.is_opd} className="w-4 h-4 rounded accent-medical-500" />
                        <span className="text-xs font-bold text-[var(--text-secondary)]">تصنيف كعيادات خارجية (OPD)</span>
                     </div>
                   </>
                 )}

                 {activeTab === 'categories' && (
                   <>
                     <div className="space-y-1">
                        <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">اسم الفئة *</label>
                        <input name="name" defaultValue={editingItem?.name} required placeholder="مثال: جناح ملكي" className="input-premium" />
                     </div>
                     <div className="space-y-1">
                        <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">التسعير اليومي (ر.س) *</label>
                        <div className="relative">
                          <input name="price" type="number" defaultValue={editingItem?.price} required placeholder="0.00" className="input-premium pe-16" />
                          <div className="absolute left-4 top-1/2 -translate-y-1/2 text-xs font-bold text-slate-400">SAR</div>
                        </div>
                     </div>
                     <div className="space-y-1">
                        <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">وصف المميزات</label>
                        <textarea name="description" defaultValue={editingItem?.description} rows={4} className="input-premium min-h-[120px] resize-none" placeholder="أدخل وصف الفئة والميزات الفندقية المصاحبة..." />
                     </div>
                   </>
                 )}

                 {activeTab === 'beds' && (
                   <div className="space-y-6">
                     <div className="space-y-1">
                        <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display px-1">كود السرير / الغرفة *</label>
                        <input name="code" defaultValue={editingItem?.code} required placeholder="B-101" className="input-premium font-mono uppercase" />
                     </div>
                     
                     <CustomCombobox 
                       label="جناح / قسم التبعية *"
                       options={wards}
                       value={selectedWard}
                       onChange={setSelectedWard}
                       placeholder="ابحث عن الجناح..."
                     />

                     <Select 
                       label="فئة السرير *"
                       options={categories}
                       value={selectedCategory}
                       onChange={setSelectedCategory}
                       placeholder="اختر الفئة..."
                     />

                     <Select 
                       label="الحالة الابتدائية *"
                       options={[
                         { id: 'AVAILABLE', name: 'متاح للاستخدام' },
                         { id: 'MAINTENANCE', name: 'تحت الصيانة' },
                         { id: 'CLEANING', name: 'جاري التعقيم' }
                       ]}
                       value={selectedStatus}
                       onChange={(val: any) => setSelectedStatus(val)}
                     />
                   </div>
                 )}

                 <div className="mt-auto pt-8 border-t border-[var(--border-color)] flex gap-4">
                   <button 
                     type="submit" 
                     disabled={isSubmitting}
                     className="flex-1 h-12 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 active:scale-95 transition-all flex items-center justify-center gap-3 text-sm"
                   >
                     {isSubmitting ? <Loader2 className="w-5 h-5 animate-spin" /> : <CheckCircle2 className="w-4 h-4" />}
                     <span>{isSubmitting ? 'جاري الحفظ...' : 'حفظ البيانات'}</span>
                   </button>
                   <button 
                     type="button" 
                     onClick={() => setIsPanelOpen(false)}
                     className="px-6 h-12 bg-slate-100 dark:bg-white/5 text-slate-500 rounded-xl font-bold transition-all text-sm border border-[var(--border-color)]"
                   >إلغاء</button>
                 </div>
               </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default FacilityManagement;
