import { graphqlRequest } from './graphqlClient';

export interface DiseaseCategory {
  id: string;
  code: string;
  name: string;
  count: number;
}

export const categoryService = {
  getCategories: async (): Promise<DiseaseCategory[]> => {
    const query = `
      query GetDiseaseCategories {
        getDiseaseCategories {
          id
          code
          name
          count
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getDiseaseCategories: DiseaseCategory[] }>(query);
      return data.getDiseaseCategories || [];
    } catch (error) {
      console.error('getCategories error:', error);
      throw error;
    }
  },

  upsertCategory: async (input: { id?: string; code: string; name: string }): Promise<DiseaseCategory> => {
    const mutation = `
      mutation UpsertDiseaseCategory($input: DiseaseCategoryInput!) {
        upsertDiseaseCategory(input: $input) {
          id
          code
          name
          count
        }
      }
    `;
    
    const variables = {
      input: {
        id: input.id || null,
        code: input.code,
        name: input.name
      }
    };

    try {
      const data = await graphqlRequest<{ upsertDiseaseCategory: DiseaseCategory }>(mutation, variables);
      return data.upsertDiseaseCategory;
    } catch (error) {
      console.error('upsertCategory error:', error);
      throw error;
    }
  },

  deleteCategory: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteDiseaseCategory($id: ID!) {
        deleteDiseaseCategory(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteDiseaseCategory: boolean }>(mutation, { id });
      return data.deleteDiseaseCategory;
    } catch (error) {
      console.error('deleteCategory error:', error);
      throw error;
    }
  }
};
