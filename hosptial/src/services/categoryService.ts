// Mocking the Category Service behaviors
export interface DiseaseCategory {
  id: string;
  code: string;
  name: string;
  count: number;
}

const STORAGE_KEY = 'medflow_disease_categories';

const DEFAULT_CATEGORIES: DiseaseCategory[] = [
  { id: '1', code: 'RESP', name: 'أمراض الجهاز التنفسي', count: 12 },
  { id: '2', code: 'CIRC', name: 'أمراض الجهاز الدوري', count: 8 },
  { id: '3', code: 'ENDO', name: 'أمراض الغدد الصماء', count: 15 },
  { id: '4', code: 'DIGE', name: 'أمراض الجهاز الهضمي', count: 6 },
  { id: '5', code: 'MUSC', name: 'أمراض الجهاز العضلي الهيكلي', count: 10 },
];

export const categoryService = {
  getCategories: async (): Promise<DiseaseCategory[]> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_CATEGORIES));
      return DEFAULT_CATEGORIES;
    }
    return JSON.parse(stored);
  },

  upsertCategory: async (input: { id?: string; code: string; name: string }): Promise<DiseaseCategory> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    const stored = await categoryService.getCategories();
    
    let updated: DiseaseCategory;
    if (input.id) {
      const index = stored.findIndex(c => c.id === input.id);
      updated = { ...stored[index], code: input.code, name: input.name };
      if (index !== -1) stored[index] = updated;
    } else {
      updated = { 
        id: Math.random().toString(36).substring(7), 
        code: input.code, 
        name: input.name,
        count: 0
      };
      stored.push(updated);
    }
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    return updated;
  },

  deleteCategory: async (id: string): Promise<boolean> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    const stored = await categoryService.getCategories();
    const filtered = stored.filter(c => c.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return true;
  }
};
