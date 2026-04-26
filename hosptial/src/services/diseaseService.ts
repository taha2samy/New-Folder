// Mocking the GraphQL Aggregator Service behaviors
// Real implementations would use @apollo/client or tanstack-query

export interface Disease {
  id: string;
  code: string;
  description: string;
  disease_type: string;
}

const STORAGE_KEY = 'medflow_diseases';

const DEFAULT_DISEASES: Disease[] = [
  { id: '1', code: 'J06.9', description: 'عدوى الجهاز التنفسي العلوي الحادة، غير محددة', disease_type: 'أمراض الجهاز التنفسي' },
  { id: '2', code: 'I10', description: 'ارتفاع ضغط الدم الأساسي (الأولي)', disease_type: 'أمراض الجهاز الدوري' },
  { id: '3', code: 'E11.9', description: 'داء السكري من النوع 2 بدون مضاعفات', disease_type: 'أمراض الغدد الصماء والتمثيل الغذائي' },
  { id: '4', code: 'K29.7', description: 'التهاب المعدة، غير محدد', disease_type: 'أمراض الجهاز الهضمي' },
  { id: '5', code: 'M54.5', description: 'آلام أسفل الظهر', disease_type: 'أمراض الجهاز العضلي الهيكلي' },
];

export const diseaseService = {
  // Query: getDiseases
  getDiseases: async (): Promise<Disease[]> => {
    // Simulate network delay
    await new Promise(resolve => setTimeout(resolve, 800));
    const stored = localStorage.getItem(STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(DEFAULT_DISEASES));
      return DEFAULT_DISEASES;
    }
    return JSON.parse(stored);
  },

  // Mutation: upsertDisease
  upsertDisease: async (input: { disease_id?: string | null; code: string; description: string; disease_type: string }): Promise<Disease> => {
    await new Promise(resolve => setTimeout(resolve, 1000));
    const stored = await diseaseService.getDiseases();
    
    let updated: Disease;
    if (input.disease_id) {
      // Edit
      updated = { id: input.disease_id, code: input.code, description: input.description, disease_type: input.disease_type };
      const index = stored.findIndex(d => d.id === input.disease_id);
      if (index !== -1) {
        stored[index] = updated;
      }
    } else {
      // Add
      updated = { 
        id: Math.random().toString(36).substring(7), 
        code: input.code, 
        description: input.description, 
        disease_type: input.disease_type 
      };
      stored.push(updated);
    }
    
    localStorage.setItem(STORAGE_KEY, JSON.stringify(stored));
    return updated;
  },

  // Mutation: deleteDisease
  deleteDisease: async (id: string): Promise<boolean> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    const stored = await diseaseService.getDiseases();
    const filtered = stored.filter(d => d.id !== id);
    localStorage.setItem(STORAGE_KEY, JSON.stringify(filtered));
    return true;
  }
};
