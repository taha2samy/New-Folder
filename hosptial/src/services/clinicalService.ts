import { graphqlRequest } from './graphqlClient';

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

export const clinicalService = {
  getExams: async (): Promise<LabExam[]> => {
    const query = `
      query GetExamTypes {
        getExamTypes {
          id
          code
          description
          procedure_type
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getExamTypes: LabExam[] }>(query);
      return data.getExamTypes || [];
    } catch (error) {
      console.error('getExams error:', error);
      throw error;
    }
  },

  upsertExam: async (input: { id?: string; code: string; description: string; procedure_type: number }): Promise<LabExam> => {
    const mutation = `
      mutation UpsertExamType($input: ExamTypeInput!) {
        upsertExamType(input: $input) {
          id
          code
          description
          procedure_type
        }
      }
    `;
    
    const variables = {
      input: {
        id: input.id || null,
        code: input.code,
        description: input.description,
        procedure_type: input.procedure_type
      }
    };

    try {
      const data = await graphqlRequest<{ upsertExamType: LabExam }>(mutation, variables);
      return data.upsertExamType;
    } catch (error) {
      console.error('upsertExam error:', error);
      throw error;
    }
  },

  deleteExam: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteExamType($id: ID!) {
        deleteExamType(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteExamType: boolean }>(mutation, { id });
      return data.deleteExamType;
    } catch (error) {
      console.error('deleteExam error:', error);
      throw error;
    }
  },

  getOperations: async (): Promise<SurgicalOperation[]> => {
    const query = `
      query GetOperationTypes {
        getOperationTypes {
          id
          code
          description
          is_major
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getOperationTypes: SurgicalOperation[] }>(query);
      return data.getOperationTypes || [];
    } catch (error) {
      console.error('getOperations error:', error);
      throw error;
    }
  },

  upsertOperation: async (input: { id?: string; code: string; description: string; is_major: boolean }): Promise<SurgicalOperation> => {
    const mutation = `
      mutation UpsertOperationType($input: OperationTypeInput!) {
        upsertOperationType(input: $input) {
          id
          code
          description
          is_major
        }
      }
    `;
    
    const variables = {
      input: {
        id: input.id || null,
        code: input.code,
        description: input.description,
        is_major: input.is_major
      }
    };

    try {
      const data = await graphqlRequest<{ upsertOperationType: SurgicalOperation }>(mutation, variables);
      return data.upsertOperationType;
    } catch (error) {
      console.error('upsertOperation error:', error);
      throw error;
    }
  },

  deleteOperation: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteOperationType($id: ID!) {
        deleteOperationType(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteOperationType: boolean }>(mutation, { id });
      return data.deleteOperationType;
    } catch (error) {
      console.error('deleteOperation error:', error);
      throw error;
    }
  }
};
