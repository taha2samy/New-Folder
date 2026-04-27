import { graphqlRequest } from './graphqlClient';

export interface Disease {
  id: string;
  code: string;
  description: string;
  disease_type: string;
}

export const diseaseService = {
  // Query: getDiseases
  getDiseases: async (): Promise<Disease[]> => {
    const query = `
      query GetDiseases {
        getDiseases {
          id
          code
          description
          disease_type
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getDiseases: Disease[] }>(query);
      return data.getDiseases || [];
    } catch (error) {
      console.error('getDiseases error:', error);
      throw error;
    }
  },

  // Mutation: upsertDisease
  upsertDisease: async (input: { disease_id?: string | null; code: string; description: string; disease_type: string }): Promise<Disease> => {
    const mutation = `
      mutation UpsertDisease($input: DiseaseInput!) {
        upsertDisease(input: $input) {
          id
          code
          description
          disease_type
        }
      }
    `;
    
    const variables = {
      input: {
        id: input.disease_id || null,
        code: input.code,
        description: input.description,
        disease_type: input.disease_type
      }
    };

    try {
      const data = await graphqlRequest<{ upsertDisease: Disease }>(mutation, variables);
      return data.upsertDisease;
    } catch (error) {
      console.error('upsertDisease error:', error);
      throw error;
    }
  },

  // Mutation: deleteDisease
  deleteDisease: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteDisease($id: ID!) {
        deleteDisease(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteDisease: boolean }>(mutation, { id });
      return data.deleteDisease;
    } catch (error) {
      console.error('deleteDisease error:', error);
      throw error;
    }
  }
};
