export interface LabExam {
  id: string;
  code: string;
  description: string;
  procedure_type: number; // 1: Single, 2: Options, 3: Free Text
}

export interface SurgicalOperation {
  id: string;
  code: string;
  description: string;
  is_major: boolean;
}

const EXAM_STORAGE_KEY = 'medflow_lab_exams';
const OP_STORAGE_KEY = 'medflow_surgical_operations';

const DEFAULT_EXAMS: LabExam[] = [
  { id: '1', code: 'CBC', description: 'صورة دم كاملة', procedure_type: 1 },
  { id: '2', code: 'GLU', description: 'سكر صائم', procedure_type: 1 },
  { id: '3', code: 'URIN', description: 'تحليل بول كامل', procedure_type: 3 },
];

const DEFAULT_OPS: SurgicalOperation[] = [
  { id: '1', code: 'APP-01', description: 'استئصال الزائدة الدودية', is_major: true },
  { id: '2', code: 'HERN-02', description: 'إصلاح فتق إربي', is_major: false },
];

export const clinicalService = {
  getExams: async (): Promise<LabExam[]> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    const stored = localStorage.getItem(EXAM_STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(EXAM_STORAGE_KEY, JSON.stringify(DEFAULT_EXAMS));
      return DEFAULT_EXAMS;
    }
    return JSON.parse(stored);
  },

  upsertExam: async (input: { id?: string; code: string; description: string; procedure_type: number }): Promise<LabExam> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    const stored = await clinicalService.getExams();
    let updated: LabExam;
    if (input.id) {
      const index = stored.findIndex(e => e.id === input.id);
      updated = { id: input.id, code: input.code, description: input.description, procedure_type: input.procedure_type };
      if (index !== -1) stored[index] = updated;
    } else {
      updated = { id: Math.random().toString(36).substring(7), ...input };
      stored.push(updated);
    }
    localStorage.setItem(EXAM_STORAGE_KEY, JSON.stringify(stored));
    return updated;
  },

  deleteExam: async (id: string): Promise<boolean> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    const stored = await clinicalService.getExams();
    const filtered = stored.filter(e => e.id !== id);
    localStorage.setItem(EXAM_STORAGE_KEY, JSON.stringify(filtered));
    return true;
  },

  getOperations: async (): Promise<SurgicalOperation[]> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    const stored = localStorage.getItem(OP_STORAGE_KEY);
    if (!stored) {
      localStorage.setItem(OP_STORAGE_KEY, JSON.stringify(DEFAULT_OPS));
      return DEFAULT_OPS;
    }
    return JSON.parse(stored);
  },

  upsertOperation: async (input: { id?: string; code: string; description: string; is_major: boolean }): Promise<SurgicalOperation> => {
    await new Promise(resolve => setTimeout(resolve, 800));
    const stored = await clinicalService.getOperations();
    let updated: SurgicalOperation;
    if (input.id) {
      const index = stored.findIndex(o => o.id === input.id);
      updated = { id: input.id, code: input.code, description: input.description, is_major: input.is_major };
      if (index !== -1) stored[index] = updated;
    } else {
      updated = { id: Math.random().toString(36).substring(7), ...input };
      stored.push(updated);
    }
    localStorage.setItem(OP_STORAGE_KEY, JSON.stringify(stored));
    return updated;
  },

  deleteOperation: async (id: string): Promise<boolean> => {
    await new Promise(resolve => setTimeout(resolve, 600));
    const stored = await clinicalService.getOperations();
    const filtered = stored.filter(o => o.id !== id);
    localStorage.setItem(OP_STORAGE_KEY, JSON.stringify(filtered));
    return true;
  }
};
