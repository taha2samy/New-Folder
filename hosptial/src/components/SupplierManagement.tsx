import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Plus, 
  Search, 
  MapPin, 
  Mail, 
  X, 
  ChevronRight,
  Filter,
  Trash2,
  Edit3,
  Loader2,
  AlertCircle
} from 'lucide-react';
import { supplierService, Supplier } from '../services/supplierService';
import { useToast } from '../lib/toast';

const SupplierManagement: React.FC<{ onBack: () => void; initialPanelState?: { open: boolean, mode: 'add' | 'edit', supplier?: Supplier } }> = ({ onBack, initialPanelState }) => {
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  const [isPanelOpen, setIsPanelOpen] = useState(initialPanelState?.open ?? false);
  const [panelMode, setPanelMode] = useState<'add' | 'edit'>(initialPanelState?.mode ?? 'add');
  const [selectedSupplier, setSelectedSupplier] = useState<Supplier | undefined>(initialPanelState?.supplier);
  const [searchQuery, setSearchQuery] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const { showToast } = useToast();

  // GraphQL Query: getSuppliers
  const fetchSuppliers = async () => {
    setLoading(true);
    try {
      const data = await supplierService.getSuppliers();
      setSuppliers(data || []);
    } catch (error: any) {
      console.error('fetchSuppliers error:', error);
      showToast(`خطأ في الاتصال: ${error.message || 'فشل تحميل بيانات الموردين من Aggregator'}`, 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
  }, []);

  const filteredSuppliers = (suppliers || []).filter(s => {
    if (!s) return false;
    const nameStr = s.name || '';
    const addressStr = s.address || '';
    const query = searchQuery || '';
    return nameStr.includes(query) || addressStr.includes(query);
  });

  // GraphQL Mutation: handleDelete
  const handleDelete = async (id: string) => {
    setIsSubmitting(true);
    try {
      await supplierService.deleteSupplier(id);
      setSuppliers(prev => prev.filter(s => s.id !== id));
      showToast('تم حذف المورد من السجل بنجاح');
      setShowDeleteConfirm(null);
    } catch (err: any) {
      console.error('handleDelete error:', err);
      showToast(`فشل الحذف: ${err.message || 'خطأ في Aggregator'}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  // GraphQL Mutation: handleSave
  const handleSave = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const data = {
      name: formData.get('name') as string,
      address: formData.get('address') as string,
      contact_info: formData.get('contact_info') as string,
    };

    if (!data.name || !data.address) {
      showToast('يرجى ملء الحقول المطلوبة', 'error');
      return;
    }

    setIsSubmitting(true);
    try {
      const result = await supplierService.upsertSupplier({ ...data, id: selectedSupplier?.id });
      if (selectedSupplier) {
        setSuppliers(prev => prev.map(s => s.id === result.id ? result : s));
      } else {
        setSuppliers(prev => [result, ...prev]);
      }
      showToast(selectedSupplier ? 'تم تحديث بيانات المورد بنجاح' : 'تم إضافة مورد جديد بنجاح');
      setIsPanelOpen(false);
    } catch (err: any) {
      console.error('handleSave error:', err);
      showToast(`فشل الحفظ: ${err.message || 'خطأ في Aggregator'}`, 'error');
    } finally {
      setIsSubmitting(false);
    }
  };

  const openAdd = () => {
    setSelectedSupplier(undefined);
    setPanelMode('add');
    setIsPanelOpen(true);
  };

  const openEdit = (supplier: Supplier) => {
    setSelectedSupplier(supplier);
    setPanelMode('edit');
    setIsPanelOpen(true);
  };

  return (
    <div className="space-y-6 pb-20 relative min-h-full" dir="rtl">
      {/* Top Header & Breadcrumbs */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex flex-col gap-1">
          <nav className="flex items-center gap-2 text-xs font-bold text-slate-400 mb-1">
            <button onClick={onBack} className="hover:text-medical-500 transition-colors">مركز البيانات</button>
            <ChevronRight className="w-3 h-3 rotate-180" />
            <span className="text-[var(--text-primary)]">سجل الموردين المعتمدين</span>
          </nav>
          <h2 className="text-2xl font-display font-bold text-[var(--text-primary)]">إدارة الموردين</h2>
        </div>
        
        <div className="flex items-center gap-3">
          <div className="relative group flex-1 md:w-64">
             <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 group-focus-within:text-medical-500 transition-colors" />
             <input 
               type="text" 
               placeholder="ابحث بالاسم أو العنوان..."
               value={searchQuery}
               onChange={(e) => setSearchQuery(e.target.value)}
               className="w-full bg-white dark:bg-white/5 border border-[var(--border-color)] rounded-xl py-2.5 pr-10 pl-4 text-xs focus:outline-none focus:border-medical-500 transition-all font-sans"
             />
          </div>
          <button className="p-2.5 bg-white dark:bg-white/5 border border-[var(--border-color)] rounded-xl text-slate-500 hover:text-medical-500 transition-all">
            <Filter className="w-4 h-4" />
          </button>
          <button 
            onClick={openAdd}
            className="flex items-center gap-2 px-6 py-2.5 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 hover:scale-105 active:scale-95 transition-all text-sm whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            <span>إضافة مورد جديد</span>
          </button>
        </div>
      </div>

      {/* Grid of Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 min-h-[400px] relative">
        <AnimatePresence mode="popLayout">
          {loading ? (
             [...Array(4)].map((_, i) => (
                <div key={i} className="card-premium p-6 h-[320px] animate-pulse">
                   <div className="flex justify-between mb-6">
                      <div className="w-12 h-12 bg-slate-100 dark:bg-slate-800 rounded-2xl"></div>
                      <div className="w-16 h-6 bg-slate-100 dark:bg-slate-800 rounded-lg"></div>
                   </div>
                   <div className="h-6 w-3/4 bg-slate-100 dark:bg-slate-800 rounded mb-2"></div>
                   <div className="h-4 w-1/2 bg-slate-100 dark:bg-slate-800 rounded mb-4"></div>
                   <div className="h-4 w-full bg-slate-100 dark:bg-slate-800 rounded mb-6"></div>
                   <div className="h-12 w-full bg-slate-100 dark:bg-slate-800 rounded-lg"></div>
                </div>
             ))
          ) : filteredSuppliers.map((supplier) => (
            <motion.div
              layout
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0, scale: 0.9 }}
              key={supplier.id}
              className="card-premium p-0 group flex flex-col h-full bg-[var(--card-bg)] border border-[var(--border-color)] hover:border-medical-500 transition-all overflow-hidden"
            >
              {/* Header Section */}
              <div className="px-6 py-4 bg-slate-50 dark:bg-white/5 border-b border-[var(--border-color)]">
                <h3 className="font-display font-bold text-lg text-[var(--text-primary)] leading-tight group-hover:text-medical-600 transition-colors">
                  {supplier.name}
                </h3>
              </div>

              {/* Body Section (Structured Info) */}
              <div className="p-6 flex-1 space-y-6">
                {supplier.address && (
                  <div className="space-y-1.5">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-display">العنوان</p>
                    <p className="text-sm text-[var(--text-primary)] leading-relaxed">{supplier.address}</p>
                  </div>
                )}

                {supplier.contact_info && (
                  <div className="space-y-1.5 pt-4 border-t border-slate-100 dark:border-white/5">
                    <p className="text-[10px] font-bold text-slate-400 uppercase tracking-wider font-display">بيانات التواصل</p>
                    <p className="text-sm text-[var(--text-primary)] leading-relaxed font-mono">{supplier.contact_info}</p>
                  </div>
                )}
              </div>

              {/* Action Bar */}
              <div className="px-4 py-3 border-t border-[var(--border-color)] flex items-center justify-between bg-slate-50/50 dark:bg-white/2">
                <button 
                  onClick={() => openEdit(supplier)}
                  className="flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold text-slate-600 dark:text-slate-400 hover:text-medical-600 hover:bg-medical-500/5 rounded-lg transition-all"
                >
                  <Edit3 className="w-3.5 h-3.5" />
                  <span>تعديل</span>
                </button>
                <div className="w-px h-6 bg-[var(--border-color)]"></div>
                <button 
                  onClick={() => setShowDeleteConfirm(supplier.id)}
                  className="flex-1 flex items-center justify-center gap-2 py-2 text-xs font-bold text-slate-600 dark:text-slate-400 hover:text-red-500 hover:bg-red-500/5 rounded-lg transition-all"
                >
                  <Trash2 className="w-3.5 h-3.5" />
                  <span>حذف</span>
                </button>
              </div>
            </motion.div>
          ))}
        </AnimatePresence>

        {!loading && filteredSuppliers.length === 0 && (
           <div className="col-span-full py-24 flex flex-col items-center justify-center text-center">
              <div className="w-24 h-24 bg-slate-100 dark:bg-white/5 rounded-full flex items-center justify-center mb-6">
                <Search className="w-10 h-10 text-slate-300" />
              </div>
              <h3 className="text-xl font-display font-bold text-[var(--text-primary)]">لا يوجد موردين مطابقين</h3>
              <p className="text-[var(--text-secondary)] mt-1 max-w-sm">لم نتمكن من العثور على أي نتائج لبحثك. حاول تغيير الكلمات المفتاحية أو إضافة مورد جديد.</p>
              <button 
                onClick={openAdd}
                className="mt-8 px-8 py-2.5 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 transition-all hover:scale-105"
              >
                إضافة مورد الآن
              </button>
           </div>
        )}
      </div>

      {/* Right Slide-over Panel (Slides from Left in RTL) */}
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
                  {panelMode === 'add' ? 'إضافة مورد جديد' : 'تعديل بيانات المورد'}
                </h3>
                <button 
                  onClick={() => setIsPanelOpen(false)}
                  className="p-2 hover:bg-slate-100 dark:hover:bg-white/5 rounded-lg transition-colors"
                >
                  <X className="w-6 h-6 text-slate-500" />
                </button>
              </div>

              <form onSubmit={handleSave} className="space-y-8 flex-1 overflow-y-auto pr-1">
                <div className="space-y-6">
                  <div className="space-y-1">
                     <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">اسم المورد *</label>
                     <input 
                      name="name"
                      defaultValue={selectedSupplier?.name}
                      autoFocus
                      type="text" 
                      className="input-premium" 
                      placeholder="أدخل الاسم الرسمي للمنشأة" 
                      required
                    />
                  </div>

                  <div className="space-y-1">
                     <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">العنوان الكامل *</label>
                     <textarea 
                      name="address"
                      defaultValue={selectedSupplier?.address}
                      className="input-premium min-h-[120px] resize-none" 
                      placeholder="المدينة، الحي، الشارع، رقم المبنى..."
                      required
                    ></textarea>
                  </div>

                  <div className="space-y-1">
                     <label className="text-[11px] font-bold text-slate-500 dark:text-slate-400 font-display">بيانات التواصل *</label>
                     <textarea 
                      name="contact_info"
                      defaultValue={selectedSupplier?.contact_info}
                      className="input-premium min-h-[100px] resize-none" 
                      placeholder="رقم الهاتف، البريد الإلكتروني، أو أي وسيلة تواصل أخرى..."
                      required
                    ></textarea>
                  </div>
                </div>

                <div className="mt-auto pt-8 border-t border-[var(--border-color)] flex gap-4 bg-transparent">
                  <button 
                    type="submit"
                    disabled={isSubmitting}
                    className="flex-1 py-3 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                  >
                    {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                    <span>{isSubmitting ? 'جاري الحفظ...' : (panelMode === 'add' ? 'حفظ المورد' : 'تحديث البيانات')}</span>
                  </button>
                  <button 
                    type="button"
                    onClick={() => setIsPanelOpen(false)}
                    disabled={isSubmitting}
                    className="flex-1 py-3 bg-slate-100 dark:bg-stone-800 text-slate-600 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-200 transition-colors"
                  >إلغاء</button>
                </div>
              </form>
            </motion.div>
          </>
        )}
      </AnimatePresence>

      {/* Delete Confirmation Modal */}
      <AnimatePresence>
        {showDeleteConfirm && (
          <>
            <motion.div 
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="fixed inset-0 bg-black/60 backdrop-blur-sm z-[100]"
            />
            <motion.div 
               initial={{ opacity: 0, scale: 0.9, y: 20 }}
               animate={{ opacity: 1, scale: 1, y: 0 }}
               exit={{ opacity: 0, scale: 0.9, y: 20 }}
               className="fixed left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 w-full max-w-sm bg-[var(--card-bg)] rounded-3xl p-8 z-[110] shadow-2xl border border-[var(--border-color)]"
            >
              <div className="w-16 h-16 bg-red-500/10 rounded-2xl flex items-center justify-center text-red-500 mb-6 mx-auto">
                <Trash2 className="w-8 h-8" />
              </div>
              <h3 className="text-xl font-display font-bold text-center mb-2">تأكيد حذف المورد؟</h3>
              <p className="text-sm text-slate-500 text-center mb-8 font-medium">سيتم حذف المورد "{suppliers.find(s => s.id === showDeleteConfirm)?.name}" من السجل الرئيسي. هل تود الاستمرار؟</p>
              <div className="flex gap-4">
                <button 
                  disabled={isSubmitting}
                  onClick={() => handleDelete(showDeleteConfirm)}
                  className="flex-1 py-3 bg-red-500 text-white rounded-xl font-bold shadow-lg shadow-red-500/20 active:scale-95 transition-all flex items-center justify-center gap-2"
                >
                  {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                  <span>نعم، حذف المورد</span>
                </button>
                <button 
                   onClick={() => setShowDeleteConfirm(null)}
                   disabled={isSubmitting}
                   className="flex-1 py-3 bg-slate-100 dark:bg-stone-800 text-slate-600 dark:text-slate-300 rounded-xl font-bold hover:bg-slate-200 transition-colors"
                >تراجع</button>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </div>
  );
};

export default SupplierManagement;
