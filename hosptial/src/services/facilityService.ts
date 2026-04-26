export interface Ward {
  id: string;
  code: string;
  name: string;
  is_opd: boolean;
  beds_count?: number; // Calculated dynamically in the UI or fetcher
}

export interface BedCategory {
  id: string;
  name: string;
  description: string;
  price: number;
}

export type BedStatus = 'AVAILABLE' | 'OCCUPIED' | 'CLEANING' | 'MAINTENANCE';

export interface Bed {
  id: string;
  code: string;
  ward_id: string;
  category_id: string;
  status: BedStatus;
  patient_name?: string;
}

const STORAGE_KEYS = {
  WARDS: 'medflow_v2_wards',
  CATEGORIES: 'medflow_v2_categories',
  BEDS: 'medflow_v2_beds',
};

const DEFAULT_CATEGORIES: BedCategory[] = [
  { id: 'cat-1', name: 'جناح VIP', description: 'إقامة فاخرة مع خدمات فندقية متكاملة', price: 2500 },
  { id: 'cat-2', name: 'غرفة خاصة', description: 'غرفة منفردة مجهزة بالكامل', price: 1200 },
  { id: 'cat-3', name: 'غرفة مشتركة', description: 'إقامة في غرفة مزدوجة معيارية', price: 600 },
  { id: 'cat-4', name: 'وحدة العناية (ICU)', description: 'تجهيزات طبية متقدمة للمراقبة المستمرة', price: 4500 },
];

const DEFAULT_WARDS: Ward[] = [
  { id: 'w-1', code: 'W-SURG', name: 'قسم الجراحة العامة', is_opd: false },
  { id: 'w-2', code: 'W-PED', name: 'قسم الأطفال', is_opd: false },
  { id: 'w-3', code: 'W-OPD-1', name: 'مجمع العيادات الخارجية', is_opd: true },
];

const DEFAULT_BEDS: Bed[] = [
  { id: 'b-1', code: 'G-101', ward_id: 'w-1', category_id: 'cat-2', status: 'AVAILABLE' },
  { id: 'b-2', code: 'G-102', ward_id: 'w-1', category_id: 'cat-3', status: 'OCCUPIED', patient_name: 'محمد عبدالله' },
  { id: 'b-3', code: 'V-501', ward_id: 'w-2', category_id: 'cat-1', status: 'CLEANING' },
];

const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms));

export const facilityService = {
  // Wards
  getWards: async (): Promise<Ward[]> => {
    await delay(500);
    const stored = localStorage.getItem(STORAGE_KEYS.WARDS);
    const wards: Ward[] = stored ? JSON.parse(stored) : DEFAULT_WARDS;
    
    // Calculate beds_count dynamically
    const beds = await facilityService.getBeds();
    return wards.map(w => ({
      ...w,
      beds_count: beds.filter(b => b.ward_id === w.id).length
    }));
  },

  upsertWard: async (input: Omit<Ward, 'id' | 'beds_count'> & { id?: string }): Promise<Ward> => {
    await delay(700);
    const stored = await facilityService.getWards();
    let result: Ward;
    
    if (input.id) {
      const index = stored.findIndex(w => w.id === input.id);
      result = { ...input, id: input.id };
      if (index !== -1) stored[index] = result;
    } else {
      result = { ...input, id: `ward-${Math.random().toString(36).substr(2, 9)}` };
      stored.push(result);
    }
    
    localStorage.setItem(STORAGE_KEYS.WARDS, JSON.stringify(stored));
    return result;
  },

  deleteWard: async (id: string): Promise<boolean> => {
    await delay(500);
    const stored = await facilityService.getWards();
    const filtered = stored.filter(w => w.id !== id);
    localStorage.setItem(STORAGE_KEYS.WARDS, JSON.stringify(filtered));
    return true;
  },

  // Categories
  getCategories: async (): Promise<BedCategory[]> => {
    await delay(500);
    const stored = localStorage.getItem(STORAGE_KEYS.CATEGORIES);
    return stored ? JSON.parse(stored) : DEFAULT_CATEGORIES;
  },

  upsertCategory: async (input: Omit<BedCategory, 'id'> & { id?: string }): Promise<BedCategory> => {
    await delay(700);
    const stored = await facilityService.getCategories();
    let result: BedCategory;
    
    if (input.id) {
      const index = stored.findIndex(c => c.id === input.id);
      result = { ...input, id: input.id };
      if (index !== -1) stored[index] = result;
    } else {
      result = { ...input, id: `cat-${Math.random().toString(36).substr(2, 9)}` };
      stored.push(result);
    }
    
    localStorage.setItem(STORAGE_KEYS.CATEGORIES, JSON.stringify(stored));
    return result;
  },

  deleteCategory: async (id: string): Promise<boolean> => {
    await delay(500);
    const stored = await facilityService.getCategories();
    localStorage.setItem(STORAGE_KEYS.CATEGORIES, JSON.stringify(stored.filter(c => c.id !== id)));
    return true;
  },

  // Beds
  getBeds: async (): Promise<Bed[]> => {
    await delay(500);
    const stored = localStorage.getItem(STORAGE_KEYS.BEDS);
    return stored ? JSON.parse(stored) : DEFAULT_BEDS;
  },

  upsertBed: async (input: Omit<Bed, 'id'> & { id?: string }): Promise<Bed> => {
    await delay(700);
    const stored = await facilityService.getBeds();
    let result: Bed;
    
    if (input.id) {
      const index = stored.findIndex(b => b.id === input.id);
      result = { ...input, id: input.id };
      if (index !== -1) stored[index] = result;
    } else {
      result = { ...input, id: `bed-${Math.random().toString(36).substr(2, 9)}` };
      stored.push(result);
    }
    
    localStorage.setItem(STORAGE_KEYS.BEDS, JSON.stringify(stored));
    return result;
  },

  deleteBed: async (id: string): Promise<boolean> => {
    await delay(500);
    const stored = await facilityService.getBeds();
    localStorage.setItem(STORAGE_KEYS.BEDS, JSON.stringify(stored.filter(b => b.id !== id)));
    return true;
  },

  updateBedStatus: async (bedId: string, status: BedStatus): Promise<boolean> => {
    await delay(400);
    const stored = await facilityService.getBeds();
    const index = stored.findIndex(b => b.id === bedId);
    if (index !== -1) {
      stored[index].status = status;
      if (status === 'AVAILABLE') stored[index].patient_name = undefined;
      localStorage.setItem(STORAGE_KEYS.BEDS, JSON.stringify(stored));
      return true;
    }
    return false;
  }
};
