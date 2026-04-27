import { graphqlRequest } from './graphqlClient';

export interface Ward {
  id: string;
  code: string;
  name: string;
  is_opd: boolean;
  beds_count?: number; 
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

export const facilityService = {
  // Wards
  getWards: async (): Promise<Ward[]> => {
    const query = `
      query GetWards {
        getWards {
          id
          code
          name
          is_opd
          beds_count
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getWards: Ward[] }>(query);
      return data.getWards || [];
    } catch (error: any) {
      if (error.message === 'MOCK_MODE') {
        return [
          { id: '1', code: 'W-01', name: 'جناح الباطنية رجال', is_opd: false, beds_count: 24 },
          { id: '2', code: 'C-01', name: 'عيادة العيون', is_opd: true, beds_count: 0 },
          { id: '3', code: 'W-02', name: 'جناح جراحة العظام', is_opd: false, beds_count: 16 },
        ];
      }
      console.error('getWards error:', error);
      throw error;
    }
  },

  upsertWard: async (input: Omit<Ward, 'id' | 'beds_count'> & { id?: string }): Promise<Ward> => {
    const mutation = `
      mutation UpsertWard($input: WardInput!) {
        upsertWard(input: $input) {
          id
          code
          name
          is_opd
          beds_count
        }
      }
    `;
    const variables = {
      input: {
        id: input.id || null,
        code: input.code,
        name: input.name,
        is_opd: input.is_opd
      }
    };
    try {
      const data = await graphqlRequest<{ upsertWard: Ward }>(mutation, variables);
      return data.upsertWard;
    } catch (error) {
      console.error('upsertWard error:', error);
      throw error;
    }
  },

  deleteWard: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteWard($id: ID!) {
        deleteWard(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteWard: boolean }>(mutation, { id });
      return data.deleteWard;
    } catch (error) {
      console.error('deleteWard error:', error);
      throw error;
    }
  },

  // Categories
  getCategories: async (): Promise<BedCategory[]> => {
    const query = `
      query GetBedCategories {
        getBedCategories {
          id
          name
          description
          price
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getBedCategories: BedCategory[] }>(query);
      return data.getBedCategories || [];
    } catch (error) {
      console.error('getCategories error:', error);
      throw error;
    }
  },

  upsertCategory: async (input: Omit<BedCategory, 'id'> & { id?: string }): Promise<BedCategory> => {
    const mutation = `
      mutation UpsertBedCategory($input: BedCategoryInput!) {
        upsertBedCategory(input: $input) {
          id
          name
          description
          price
        }
      }
    `;
    const variables = {
      input: {
        id: input.id || null,
        name: input.name,
        description: input.description,
        price: parseFloat(input.price as any)
      }
    }
    try {
      const data = await graphqlRequest<{ upsertBedCategory: BedCategory }>(mutation, variables);
      return data.upsertBedCategory;
    } catch (error) {
      console.error('upsertCategory error:', error);
      throw error;
    }
  },

  deleteCategory: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteBedCategory($id: ID!) {
        deleteBedCategory(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteBedCategory: boolean }>(mutation, { id });
      return data.deleteBedCategory;
    } catch (error) {
      console.error('deleteCategory error:', error);
      throw error;
    }
  },

  // Beds
  getBeds: async (): Promise<Bed[]> => {
    const query = `
      query GetBeds {
        getBeds {
          id
          code
          ward_id
          category_id
          status
          patient_name
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getBeds: Bed[] }>(query);
      return data.getBeds || [];
    } catch (error) {
      console.error('getBeds error:', error);
      throw error;
    }
  },

  upsertBed: async (input: Omit<Bed, 'id'> & { id?: string }): Promise<Bed> => {
    const mutation = `
      mutation UpsertBed($input: BedInput!) {
        upsertBed(input: $input) {
          id
          code
          ward_id
          category_id
          status
          patient_name
        }
      }
    `;
    const variables = {
      input: {
        id: input.id || null,
        code: input.code,
        ward_id: input.ward_id,
        category_id: input.category_id,
        status: input.status,
        patient_name: input.patient_name || null
      }
    };
    try {
      const data = await graphqlRequest<{ upsertBed: Bed }>(mutation, variables);
      return data.upsertBed;
    } catch (error) {
      console.error('upsertBed error:', error);
      throw error;
    }
  },

  deleteBed: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteBed($id: ID!) {
        deleteBed(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteBed: boolean }>(mutation, { id });
      return data.deleteBed;
    } catch (error) {
      console.error('deleteBed error:', error);
      throw error;
    }
  },

  updateBedStatus: async (bedId: string, status: BedStatus): Promise<boolean> => {
    const mutation = `
      mutation UpdateBedStatus($id: ID!, $status: BedStatus!) {
        updateBedStatus(id: $id, status: $status)
      }
    `;
    try {
      const data = await graphqlRequest<{ updateBedStatus: boolean }>(mutation, { id: bedId, status });
      return data.updateBedStatus;
    } catch (error) {
      console.error('updateBedStatus error:', error);
      throw error;
    }
  }
};
