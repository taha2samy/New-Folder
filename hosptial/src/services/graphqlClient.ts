import { useToast } from '../lib/toast';

const GRAPH_API_URL = import.meta.env.VITE_GRAPH_API_URL;
const MANUAL_TEST_TOKEN = import.meta.env.VITE_MANUAL_TEST_TOKEN;

export async function checkHealth(): Promise<{ status: 'online' | 'unreachable' | 'unauthorized' | 'not_found' | 'mock', message?: string }> {
  if (!import.meta.env.VITE_GRAPH_API_URL) return { status: 'mock' };

  try {
    const response = await fetch(import.meta.env.VITE_GRAPH_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(import.meta.env.VITE_MANUAL_TEST_TOKEN ? { 'Authorization': `Bearer ${import.meta.env.VITE_MANUAL_TEST_TOKEN}` } : {})
      },
      body: JSON.stringify({ query: '{ __typename }' })
    });

    if (response.status === 200) return { status: 'online' };
    if (response.status === 401 || response.status === 403) return { status: 'unauthorized', message: '🚫 التوكن غير صالح' };
    if (response.status === 404) return { status: 'not_found', message: '⚠️ الرابط غير صحيح (404)' };
    
    return { status: 'unreachable', message: `⚠️ خطأ في الخادم (${response.status})` };
  } catch (error) {
    console.error('Health check failed for URL:', import.meta.env.VITE_GRAPH_API_URL, error);
    return { status: 'unreachable', message: '⚠️ فشل الاتصال بالشبكة' };
  }
}

export async function graphqlRequest<T>(query: string, variables: Record<string, any> = {}): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (MANUAL_TEST_TOKEN) {
    headers['Authorization'] = `Bearer ${MANUAL_TEST_TOKEN}`;
  }

  try {
    if (!GRAPH_API_URL) {
      throw new Error('MOCK_MODE'); // Simple flag for upstream
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
      // Log technical details for developers
      console.error(`Technical Debug: Fetch failed at ${GRAPH_API_URL}`, { status: response.status, body: errorText });
      throw new Error(`HTTP_${response.status}`); // Pass status code for specialized handling
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('INVALID_CONTENT_TYPE');
    }

    const result = await response.json();

    if (result.errors) {
      console.error('GraphQL Errors:', result.errors);
      throw new Error(result.errors[0].message || 'GRAPHQL_ERROR');
    }

    return result.data;
  } catch (error: any) {
    // If it's already one of our handled types, just rethrow
    if (['MOCK_MODE', 'INVALID_CONTENT_TYPE', 'GRAPHQL_ERROR'].includes(error.message) || error.message.startsWith('HTTP_')) {
      throw error;
    }
    console.error('Network failure:', error);
    throw new Error('NETWORK_FAILURE');
  }
}
