import { useToast } from '../lib/toast';

const GRAPH_API_URL = import.meta.env.VITE_GRAPH_API_URL;
const MANUAL_TEST_TOKEN = import.meta.env.VITE_MANUAL_TEST_TOKEN;

// Create an event target to broadcast diagnostic logs
class DiagnosticEmitter extends EventTarget {}
export const diagnosticEvents = new DiagnosticEmitter();

export function logDiagnostic(type: 'SYSTEM' | 'CONFIG' | 'AUTH' | 'NETWORK' | 'ERROR' | 'RETRY', message: string, details?: any) {
  const timestamp = new Date().toISOString().substring(11, 19);
  const logStr = `[${timestamp}] [${type}] ${message}`;
  
  diagnosticEvents.dispatchEvent(new CustomEvent('log', { 
    detail: { type, message, details, logStr, timestamp } 
  }));
}

let forceMockOverride = false;

export function setForceMock(value: boolean) {
  forceMockOverride = value;
  logDiagnostic('SYSTEM', `Force Mock mode set to: ${value}`);
}

export async function checkHealth(): Promise<{ status: 'online' | 'unreachable' | 'unauthorized' | 'not_found' | 'mock', message?: string, error?: any }> {
  logDiagnostic('SYSTEM', 'Checking Environment Variables...');

  logDiagnostic('CONFIG', `VITE_GRAPH_API_URL detected as: "${import.meta.env.VITE_GRAPH_API_URL || 'NOT SET'}"`);
  logDiagnostic('AUTH', `Manual Token detected: ${import.meta.env.VITE_MANUAL_TEST_TOKEN ? 'YES (Starts with ' + import.meta.env.VITE_MANUAL_TEST_TOKEN.substring(0,10) + '...)' : 'NO'}`);

  if (!import.meta.env.VITE_GRAPH_API_URL) {
    logDiagnostic('CONFIG', 'No API URL found, defaulting to MOCK mode.');
    return { status: 'mock' };
  }

  try {
    logDiagnostic('NETWORK', 'Attempting POST request to endpoint for health check...', { 
      url: import.meta.env.VITE_GRAPH_API_URL,
      fetchConfig: {
        method: 'POST',
        mode: 'cors',
        headers: {
          'Content-Type': 'application/json',
          ...(import.meta.env.VITE_MANUAL_TEST_TOKEN ? { 'Authorization': `Bearer ${import.meta.env.VITE_MANUAL_TEST_TOKEN.substring(0, 5)}...` } : {})
        }
      }
    });
    const response = await fetch(import.meta.env.VITE_GRAPH_API_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(import.meta.env.VITE_MANUAL_TEST_TOKEN ? { 'Authorization': `Bearer ${import.meta.env.VITE_MANUAL_TEST_TOKEN}` } : {})
      },
      body: JSON.stringify({ query: '{ __typename }' })
    });

    logDiagnostic('NETWORK', `Health check response received: ${response.status} ${response.statusText}`);

    if (response.status === 200) return { status: 'online' };
    if (response.status === 401 || response.status === 403) {
      const errorMsg = '🚫 التوكن غير صالح';
      logDiagnostic('ERROR', `Unauthorized: ${response.status}`);
      return { status: 'unauthorized', message: errorMsg };
    }
    if (response.status === 404) {
      logDiagnostic('ERROR', 'Endpoint not found (404)');
      return { status: 'not_found', message: '⚠️ الرابط غير صحيح (404)' };
    }
    
    logDiagnostic('ERROR', `Server Error (${response.status})`);
    return { status: 'unreachable', message: `⚠️ خطأ في الخادم (${response.status})` };
  } catch (error: any) {
    logDiagnostic('ERROR', `Connection Failed: ${error.message || 'Unknown Network Error'}`, error);
    
    // Check for specific CORS error string
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      logDiagnostic('ERROR', '🚨 احتمال وجود مشكلة CORS - تأكد من إعدادات الـ Aggregator.');
    }
    
    return { status: 'unreachable', message: '⚠️ فشل الاتصال بالشبكة', error };
  }
}

export async function graphqlRequest<T>(query: string, variables: Record<string, any> = {}, forceMock = false): Promise<T> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };

  if (MANUAL_TEST_TOKEN) {
    headers['Authorization'] = `Bearer ${MANUAL_TEST_TOKEN}`;
  }

  try {
    if (!GRAPH_API_URL || forceMock || forceMockOverride) {
      throw new Error('MOCK_MODE'); // Simple flag for upstream
    }

    logDiagnostic('NETWORK', 'Executing GraphQL Query...', { 
      query: query.substring(0, 100) + '...', 
      variables,
      fetchConfig: {
        method: 'POST',
        mode: 'cors',
        headers
      }
    });
    
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
      logDiagnostic('ERROR', `GraphQL Request Failed with status ${response.status}`, { body: errorText });
      throw new Error(`HTTP_${response.status}`); // Pass status code for specialized handling
    }

    const contentType = response.headers.get('content-type');
    if (!contentType || !contentType.includes('application/json')) {
      throw new Error('INVALID_CONTENT_TYPE');
    }

    const result = await response.json();

    if (result.errors) {
      logDiagnostic('ERROR', 'GraphQL returned errors array', result.errors);
      throw new Error(result.errors[0].message || 'GRAPHQL_ERROR');
    }

    return result.data;
  } catch (error: any) {
    if (error.message === 'MOCK_MODE') {
      throw error;
    }
    
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      logDiagnostic('ERROR', '🚨 احتمال وجود مشكلة CORS في GraphQL Request.');
    } else if (!['INVALID_CONTENT_TYPE', 'GRAPHQL_ERROR'].includes(error.message) && !error.message.startsWith('HTTP_')) {
       logDiagnostic('ERROR', `GraphQL Network failure: ${error.message}`);
    }
    
    // If it's already one of our handled types, just rethrow
    if (['INVALID_CONTENT_TYPE', 'GRAPHQL_ERROR'].includes(error.message) || error.message.startsWith('HTTP_')) {
      throw error;
    }
    
    throw new Error('NETWORK_FAILURE');
  }
}
