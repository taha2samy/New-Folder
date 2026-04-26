import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { 
  Building2, 
  BookOpen, 
  BriefcaseMedical, 
  Truck, 
  ChevronLeft, 
  Search,
  ExternalLink,
  ClipboardList,
  Plus,
  Loader2
} from 'lucide-react';
import SupplierManagement from './SupplierManagement';
import MedicalDirectoryManagement from './MedicalDirectoryManagement';
import ClinicalServicesManagement from './ClinicalServicesManagement';
import FacilityManagement from './FacilityManagement';
import { supplierService, Supplier } from '../services/supplierService';
import { diseaseService, Disease } from '../services/diseaseService';
import { categoryService, DiseaseCategory } from '../services/categoryService';
import { clinicalService, LabExam, SurgicalOperation } from '../services/clinicalService';
import { facilityService, Ward } from '../services/facilityService';
import { useToast } from '../lib/toast';

const MasterDataHub: React.FC = () => {
  const [activeView, setActiveView] = useState<'hub' | 'suppliers' | 'medical-directory' | 'clinical-services' | 'facilities'>('hub');
  const [medicalDirSubView, setMedicalDirSubView] = useState<'diseases' | 'categories'>('diseases');
  const [clinicalSubView, setClinicalSubView] = useState<'exams' | 'operations'>('exams');
  const [initialSupplierState, setInitialSupplierState] = useState<{ open: boolean, mode: 'add' | 'edit', supplier?: Supplier } | undefined>();
  const [initialMedicalDirState, setInitialMedicalDirState] = useState<{ open: boolean, mode: 'add' | 'edit', disease?: Disease, category?: DiseaseCategory } | undefined>();
  const [initialClinicalState, setInitialClinicalState] = useState<{ activeTab: 'exams' | 'operations' } | undefined>();
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [diseases, setDiseases] = useState<Disease[]>([]);
  const [categories, setCategories] = useState<DiseaseCategory[]>([]);
  const [exams, setExams] = useState<LabExam[]>([]);
  const [operations, setOperations] = useState<SurgicalOperation[]>([]);
  const [wards, setWards] = useState<Ward[]>([]);
  const [loadingSuppliers, setLoadingSuppliers] = useState(true);
  const [loadingDiseases, setLoadingDiseases] = useState(true);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [loadingClinical, setLoadingClinical] = useState(true);
  const [loadingFacilities, setLoadingFacilities] = useState(true);
  const { showToast } = useToast();

  const fetchSuppliers = async () => {
    setLoadingSuppliers(true);
    try {
      const data = await supplierService.getSuppliers();
      setSuppliers(data.slice(0, 3)); // Only show top 3 in hub preview
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingSuppliers(false);
    }
  };

  const fetchDiseases = async () => {
    setLoadingDiseases(true);
    try {
      const data = await diseaseService.getDiseases();
      setDiseases(data.slice(0, 4)); // Only show top 4 in hub preview
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingDiseases(false);
    }
  };

  const fetchCategories = async () => {
    setLoadingCategories(true);
    try {
      const data = await categoryService.getCategories();
      setCategories(data.slice(0, 4));
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingCategories(false);
    }
  };

  const fetchClinicalData = async () => {
    setLoadingClinical(true);
    try {
      const [examData, opData] = await Promise.all([
        clinicalService.getExams(),
        clinicalService.getOperations()
      ]);
      setExams(examData.slice(0, 3));
      setOperations(opData.slice(0, 3));
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingClinical(false);
    }
  };

  const fetchFacilities = async () => {
    setLoadingFacilities(true);
    try {
      const data = await facilityService.getWards();
      setWards(data.slice(0, 4));
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingFacilities(false);
    }
  };

  useEffect(() => {
    fetchSuppliers();
    fetchDiseases();
    fetchCategories();
    fetchClinicalData();
    fetchFacilities();
  }, [activeView]);

  const goToSuppliers = (state?: { open: boolean, mode: 'add' | 'edit', supplier?: Supplier }) => {
    setInitialSupplierState(state);
    setActiveView('suppliers');
  };

  const goToMedicalDir = (state?: { open: boolean, mode: 'add' | 'edit', disease?: Disease, category?: DiseaseCategory }) => {
    setInitialMedicalDirState(state);
    setActiveView('medical-directory');
  };

  const goToClinicalServices = (tab: 'exams' | 'operations' = 'exams') => {
    setInitialClinicalState({ activeTab: tab });
    setActiveView('clinical-services');
  };

  const goToFacilities = () => {
    setActiveView('facilities');
  };

  const containerVariants = {
    hidden: { opacity: 0 },
    show: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2
      }
    }
  };

  const itemVariants = {
    hidden: { opacity: 0, y: 20 },
    show: { opacity: 1, y: 0, transition: { duration: 0.4, ease: [0.23, 1, 0.32, 1] } }
  };

  if (activeView === 'suppliers') {
    return <SupplierManagement onBack={() => setActiveView('hub')} initialPanelState={initialSupplierState} />;
  }

  if (activeView === 'medical-directory') {
    return <MedicalDirectoryManagement onBack={() => setActiveView('hub')} initialPanelState={initialMedicalDirState} />;
  }

  if (activeView === 'clinical-services') {
    return <ClinicalServicesManagement onBack={() => setActiveView('hub')} initialTab={initialClinicalState?.activeTab} />;
  }

  if (activeView === 'facilities') {
    return <FacilityManagement onBack={() => setActiveView('hub')} />;
  }

  return (
    <motion.div 
      initial={{ opacity: 0, x: 20 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: -20 }}
      className="space-y-8 pb-12" 
      dir="rtl"
    >
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-2xl font-display font-bold text-[var(--text-primary)]">مركز البيانات المرجع الرئيسي</h2>
          <p className="text-[var(--text-secondary)] mt-1">إدارة الأصول الطبية، المنشآت، والخدمات المرجعية الموحدة</p>
        </div>
        <button className="flex items-center gap-2 px-6 py-2.5 bg-medical-500 text-white rounded-xl font-bold shadow-lg shadow-medical-500/20 hover:scale-105 active:scale-95 transition-all text-sm">
          <span>سجل مرجعي جديد</span>
          <ExternalLink className="w-4 h-4" />
        </button>
      </div>

      <motion.div 
        variants={containerVariants}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 xl:grid-cols-2 gap-6"
      >
        {/* Module 1: Facilities & Infrastructure */}
        <motion.div variants={itemVariants} className="card-premium p-6 group hover:shadow-xl hover:shadow-medical-500/5 transition-all overflow-hidden relative flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-medical-500/10 text-medical-500 rounded-xl group-hover:scale-110 transition-transform">
                <Building2 className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-lg">إدارة المنشآت والبنية التحتية</h3>
            </div>
            <button 
              onClick={() => goToFacilities()}
              className="text-xs font-bold text-medical-600 hover:bg-medical-500/5 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <span>إدارة</span>
              <ChevronLeft className="w-3 h-3" />
            </button>
          </div>

          <div className="flex-1 space-y-4">
             <div className="flex items-center justify-between">
                <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider">العنابر النشطة</p>
                <div className="flex items-center gap-2">
                   <div className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                   <span className="text-[10px] font-bold text-emerald-500">مباشر</span>
                </div>
             </div>

             <div className="space-y-3">
                {loadingFacilities ? (
                  <div className="flex items-center justify-center h-40">
                    <Loader2 className="w-6 h-6 animate-spin text-medical-500" />
                  </div>
                ) : (wards || []).map((ward, i) => (
                  <div 
                    key={i} 
                    onClick={() => goToFacilities()}
                    className="flex justify-between items-center p-4 rounded-xl bg-slate-50 dark:bg-white/5 border border-transparent hover:border-[var(--border-color)] cursor-pointer transition-all"
                  >
                    <div>
                      <p className="text-[15px] font-bold text-[var(--text-primary)] leading-tight">{ward.name}</p>
                      <span className={`badge-faded mt-1 inline-block ${ward.is_opd ? 'badge-faded-blue' : 'badge-faded-emerald'}`}>
                        {ward.is_opd ? 'عيادات خارجية' : 'قسم تنويم'}
                      </span>
                    </div>
                    <div className="text-left font-display">
                       <p className="text-[10px] font-bold text-slate-400">السعة</p>
                       <p className="text-sm font-bold text-medical-500">{ward.beds_count} سرير</p>
                    </div>
                  </div>
                ))}
             </div>
          </div>
        </motion.div>

        {/* Module 2: Medical Knowledge Base (ICD-10) */}
        <motion.div variants={itemVariants} className="card-premium p-6 group hover:shadow-xl hover:shadow-medical-500/5 transition-all overflow-hidden flex flex-col">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-purple-500/10 text-purple-500 rounded-xl group-hover:scale-110 transition-transform">
                  <BookOpen className="w-5 h-5" />
                </div>
                <h3 className="font-display font-bold text-lg">الدليل الطبي الموحد (ICD-10)</h3>
              </div>
              <button 
                onClick={() => goToMedicalDir()}
                className="text-xs font-bold text-medical-600 hover:bg-medical-500/5 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
              >
                <span>إدارة</span>
                <ChevronLeft className="w-3 h-3" />
              </button>
            </div>

            {/* Segmented Control */}
            <div className="flex p-1 bg-slate-100 dark:bg-white/5 rounded-xl border border-[var(--border-color)]">
              <button 
                onClick={() => setMedicalDirSubView('diseases')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${medicalDirSubView === 'diseases' ? 'bg-white dark:bg-slate-800 shadow-sm text-medical-600' : 'text-slate-500 hover:text-slate-700'}`}
              >الأمراض</button>
              <button 
                onClick={() => setMedicalDirSubView('categories')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${medicalDirSubView === 'categories' ? 'bg-white dark:bg-slate-800 shadow-sm text-medical-600' : 'text-slate-500 hover:text-slate-700'}`}
              >التصنيفات</button>
            </div>
          </div>

          <div className="relative mb-6" onClick={() => goToMedicalDir()}>
            <Search className="absolute right-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <input 
              type="text" 
              readOnly
              placeholder={medicalDirSubView === 'diseases' ? "ابحث عن رمز مرض..." : "ابحث عن تصنيف..."}
              className="w-full bg-slate-100/50 dark:bg-white/5 border border-[var(--border-color)] rounded-xl py-2.5 pr-10 pl-4 text-xs focus:outline-none focus:border-medical-500 transition-all font-sans cursor-pointer"
            />
          </div>

          <div className="flex-1 space-y-3">
             <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
               {medicalDirSubView === 'diseases' ? 'الرموز الأكثر استخداماً' : 'التصنيفات الطبية'}
             </p>
             
             {medicalDirSubView === 'diseases' ? (
                loadingDiseases ? (
                  <div className="flex items-center justify-center h-40">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
                  </div>
                ) : (diseases || []).map((code, i) => (
                  <div 
                    key={i} 
                    onClick={() => goToMedicalDir({ open: true, mode: 'edit', disease: code })}
                    className="flex items-center gap-4 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer border border-transparent hover:border-[var(--border-color)] transition-all group/row"
                  >
                    <span className="badge-hollow group-hover/row:border-medical-500/30 group-hover/row:text-medical-500 transition-colors shrink-0">
                      {code.code}
                    </span>
                    <div className="flex-1">
                      <p className="text-[14px] font-bold text-[var(--text-primary)] line-clamp-1">{code.description}</p>
                      <span className="text-[10px] text-[var(--text-secondary)] mt-0.5 block">{code.disease_type}</span>
                    </div>
                    <ChevronLeft className="w-3.5 h-3.5 text-slate-300" />
                  </div>
                ))
             ) : (
                loadingCategories ? (
                  <div className="flex items-center justify-center h-40">
                    <Loader2 className="w-6 h-6 animate-spin text-purple-500" />
                  </div>
                ) : (categories || []).map((cat, i) => (
                  <div 
                    key={i} 
                    onClick={() => goToMedicalDir({ open: true, mode: 'edit', category: cat })}
                    className="flex items-center gap-4 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer border border-transparent hover:border-[var(--border-color)] transition-all"
                  >
                    <div className="w-8 h-8 rounded-lg bg-purple-500/10 flex items-center justify-center text-purple-600 font-bold text-[10px] uppercase">
                      {cat.code}
                    </div>
                    <div className="flex-1">
                      <p className="text-[13px] font-bold">{cat.name}</p>
                      <span className="text-[10px] text-slate-500 mt-0.5 block">{cat.count} رمز طبي مرتبط</span>
                    </div>
                    <ChevronLeft className="w-3.5 h-3.5 text-slate-300" />
                  </div>
                ))
             )}
          </div>
        </motion.div>

        {/* Module 3: Service & Procedure Catalog */}
        <motion.div variants={itemVariants} className="card-premium p-6 group hover:shadow-xl hover:shadow-medical-500/5 transition-all overflow-hidden flex flex-col">
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div className="flex items-center gap-3">
                <div className="p-2.5 bg-emerald-500/10 text-emerald-500 rounded-xl group-hover:scale-110 transition-transform">
                  <BriefcaseMedical className="w-5 h-5" />
                </div>
                <h3 className="font-display font-bold text-lg">دليل الخدمات والعمليات الإكلينيكية</h3>
              </div>
              <button 
                onClick={() => goToClinicalServices(clinicalSubView)}
                className="text-xs font-bold text-medical-600 hover:bg-medical-500/5 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
              >
                <span>إدارة</span>
                <ChevronLeft className="w-3 h-3" />
              </button>
            </div>

            {/* Segmented Control */}
            <div className="flex p-1 bg-slate-100 dark:bg-white/5 rounded-xl border border-[var(--border-color)]">
              <button 
                onClick={() => setClinicalSubView('exams')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${clinicalSubView === 'exams' ? 'bg-white dark:bg-slate-800 shadow-sm text-medical-600' : 'text-slate-500 hover:text-slate-700'}`}
              >الفحوصات المخبرية</button>
              <button 
                onClick={() => setClinicalSubView('operations')}
                className={`flex-1 py-2 text-xs font-bold rounded-lg transition-all ${clinicalSubView === 'operations' ? 'bg-white dark:bg-slate-800 shadow-sm text-medical-600' : 'text-slate-500 hover:text-slate-700'}`}
              >العمليات الجراحية</button>
            </div>
          </div>

          <div className="flex-1 space-y-3">
             <p className="text-[11px] font-bold text-slate-400 uppercase tracking-wider mb-2">
               {clinicalSubView === 'exams' ? 'الفحوصات المرجعية' : 'العمليات المسجلة'}
             </p>
             
             {clinicalSubView === 'exams' ? (
                loadingClinical ? (
                  <div className="flex items-center justify-center h-40">
                    <Loader2 className="w-6 h-6 animate-spin text-emerald-500" />
                  </div>
                ) : (exams || []).map((exam, i) => (
                  <div 
                    key={i} 
                    onClick={() => goToClinicalServices('exams')}
                    className="flex items-center gap-4 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer border border-transparent hover:border-[var(--border-color)] transition-all group/row"
                  >
                    <div className="w-1 h-8 bg-emerald-500 rounded-full" />
                    <div className="flex-1">
                      <p className="text-[14px] font-bold text-[var(--text-primary)] line-clamp-1">{exam.description}</p>
                      <span className="text-[10px] text-[var(--text-secondary)] mt-0.5 block">كود: {exam.code}</span>
                    </div>
                    <ChevronLeft className="w-3.5 h-3.5 text-slate-300" />
                  </div>
                ))
             ) : (
                loadingClinical ? (
                  <div className="flex items-center justify-center h-40">
                    <Loader2 className="w-6 h-6 animate-spin text-blue-500" />
                  </div>
                ) : (operations || []).map((op, i) => (
                  <div 
                    key={i} 
                    onClick={() => goToClinicalServices('operations')}
                    className="flex items-center gap-4 p-3 rounded-xl hover:bg-slate-50 dark:hover:bg-white/5 cursor-pointer border border-transparent hover:border-[var(--border-color)] transition-all group/row"
                  >
                    <div className="w-1 h-8 bg-blue-500 rounded-full" />
                    <div className="flex-1">
                      <p className="text-[14px] font-bold text-[var(--text-primary)] line-clamp-1">{op.description}</p>
                      <div className="flex items-center gap-2 mt-0.5">
                        <span className="text-[10px] text-[var(--text-secondary)]">كود: {op.code}</span>
                        <span className={`badge-faded ${op.is_major ? 'badge-faded-red' : 'badge-faded-emerald'}`}>
                          {op.is_major ? 'كبرى' : 'صغرى'}
                        </span>
                      </div>
                    </div>
                    <ChevronLeft className="w-3.5 h-3.5 text-slate-300" />
                  </div>
                ))
             )}
          </div>
        </motion.div>

        {/* Module 4: Global Supplier Registry */}
        <motion.div variants={itemVariants} className="card-premium p-6 group hover:shadow-xl hover:shadow-medical-500/5 transition-all overflow-hidden flex flex-col">
          <div className="flex items-center justify-between mb-8">
            <div className="flex items-center gap-3">
              <div className="p-2.5 bg-amber-500/10 text-amber-500 rounded-xl group-hover:scale-110 transition-transform">
                <Truck className="w-5 h-5" />
              </div>
              <h3 className="font-display font-bold text-lg">سجل الموردين المعتمدين</h3>
            </div>
            <button 
              onClick={() => goToSuppliers()}
              className="text-xs font-bold text-medical-600 hover:bg-medical-500/5 px-3 py-1.5 rounded-lg transition-colors flex items-center gap-1.5"
            >
              <span>إدارة</span>
              <ChevronLeft className="w-3 h-3" />
            </button>
          </div>

          <div className="space-y-4 flex-1">
             {loadingSuppliers ? (
                <div className="flex items-center justify-center h-40">
                  <Loader2 className="w-6 h-6 animate-spin text-medical-500" />
                </div>
             ) : (suppliers || []).map((supplier, i) => (
               <div 
                key={i} 
                onClick={() => goToSuppliers({ open: true, mode: 'edit', supplier })}
                className="flex items-center gap-4 p-4 rounded-xl bg-slate-50 dark:bg-white/5 border border-transparent hover:border-[var(--border-color)] group/row cursor-pointer transition-all"
              >
                  <div className="w-10 h-10 rounded-full bg-white dark:bg-slate-800 flex items-center justify-center border border-[var(--border-color)]">
                    <span className="text-[14px] font-bold text-medical-600 uppercase">{supplier.name.charAt(0)}</span>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                       <p className="text-[13px] font-bold">{supplier.name}</p>
                    </div>
                    <p className="text-[11px] text-slate-500 mt-0.5 truncate max-w-[150px]">{supplier.address}</p>
                  </div>
                  <div className="text-left">
                    <span className="text-[10px] bg-slate-200 dark:bg-slate-700 px-2 py-1 rounded text-slate-600 dark:text-slate-300 font-bold group-hover/row:bg-medical-500 group-hover/row:text-white transition-colors truncate max-w-[120px] inline-block font-mono">
                      {supplier.contact_info || ''}
                    </span>
                  </div>
               </div>
             ))}
          </div>

          <button 
            onClick={() => goToSuppliers({ open: true, mode: 'add' })}
            className="w-full flex items-center justify-center gap-2 mt-6 py-3 border-2 border-dashed border-slate-200 dark:border-slate-800 rounded-xl text-xs font-bold text-slate-400 hover:border-medical-500 hover:text-medical-500 transition-all font-display"
          >
             <Plus className="w-4 h-4" />
             <span>إضافة مورد معتمد جديد</span>
          </button>
        </motion.div>
      </motion.div>

       {/* Floating Action Button (already handled in App for globally accessed actions usually, but let's keep consistent with existing UI) */}
    </motion.div>
  );
};

export default MasterDataHub;
