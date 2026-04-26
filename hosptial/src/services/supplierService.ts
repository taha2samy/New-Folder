// Mocking the GraphQL Aggregator Service behaviors
// Real implementations would use @apollo/client or tanstack-query

import { graphqlRequest } from './graphqlClient';

export interface Supplier {
  id: string;
  name: string;
  address: string;
  contact_info: string;
}

export const supplierService = {
  // Query: getSuppliers
  getSuppliers: async (): Promise<Supplier[]> => {
    const query = `
      query GetSuppliers {
        getSuppliers {
          id
          name
          address
          contact_info
        }
      }
    `;
    try {
      const data = await graphqlRequest<{ getSuppliers: Supplier[] }>(query);
      return data.getSuppliers || [];
    } catch (error) {
      console.error('getSuppliers error:', error);
      throw error;
    }
  },

  // Mutation: upsertSupplier
  upsertSupplier: async (input: Omit<Supplier, 'id'> & { id?: string }): Promise<Supplier> => {
    const mutation = `
      mutation UpsertSupplier($input: SupplierInput!) {
        upsertSupplier(input: $input) {
          id
          name
          address
          contact_info
        }
      }
    `;
    
    // Convert id to string or null for GraphQL input
    const variables = {
      input: {
        id: input.id || null,
        name: input.name,
        address: input.address,
        contact_info: input.contact_info
      }
    };

    try {
      const data = await graphqlRequest<{ upsertSupplier: Supplier }>(mutation, variables);
      return data.upsertSupplier;
    } catch (error) {
      console.error('upsertSupplier error:', error);
      throw error;
    }
  },

  // Mutation: deleteSupplier
  deleteSupplier: async (id: string): Promise<boolean> => {
    const mutation = `
      mutation DeleteSupplier($id: ID!) {
        deleteSupplier(id: $id)
      }
    `;
    try {
      const data = await graphqlRequest<{ deleteSupplier: boolean }>(mutation, { id });
      return data.deleteSupplier;
    } catch (error) {
      console.error('deleteSupplier error:', error);
      throw error;
    }
  }
};
