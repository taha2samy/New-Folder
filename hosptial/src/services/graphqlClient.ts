import { useToast } from '../lib/toast';

const GRAPH_API_URL = import.meta.env.VITE_GRAPH_API_URL;
const MANUAL_TEST_TOKEN = import.meta.env.VITE_MANUAL_TEST_TOKEN;

export async function graphqlRequest<T>(query: string, variables: Record<string, any> = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (MANUAL_TEST_TOKEN) {
    headers['Authorization'] = `Bearer ${MANUAL_TEST_TOKEN}`;
  }

  try {
    if (!GRAPH_API_URL) {
      throw new Error('VITE_GRAPH_API_URL is not defined in environment variables');
    }

    const response = await fetch(GRAPH_API_URL, {
      method: 'POST',
      headers,
      body: JSON.stringify({
        query,
        variables,
      }),
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP Error ${response.status}: ${errorText || response.statusText}`);
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      const text = await response.text();
      throw new Error(`Expected JSON but received ${contentType || 'nothing'}: ${text.substring(0, 100)}`);
    }

    const result = await response.json();

    if (result.errors) {
      console.error('GraphQL Errors:', result.errors);
      throw new Error(result.errors[0].message || 'GraphQL Request failed');
    }

    return result.data;
  } catch (error: any) {
    console.error('Network or GraphQL Error:', error);
    throw error;
  }
}
