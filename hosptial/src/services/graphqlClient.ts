import { useToast } from '../lib/toast';

const GRAPH_API_URL = import.meta.env.VITE_GRAPH_API_URL;
const MANUAL_TEST_TOKEN = import.meta.env.VITE_MANUAL_TEST_TOKEN;

// Create an event target to broadcast diagnostic logs
class DiagnosticEmitter extends EventTarget {}
export const diagnosticEvents = new DiagnosticEmitter();

export function logDiagnostic(type: 'SYSTEM' | 'CONFIG' | 'AUTH' | 'NETWORK' | 'ERROR' | 'RETRY' | 'MODE' | 'CHECK', message: string, details?: any) {
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

  const useMock = import.meta.env.VITE_USE_MOCK === 'true';
  const apiUrl = import.meta.env.VITE_GRAPH_API_URL || 'NOT SET';
  const hasToken = !!import.meta.env.VITE_MANUAL_TEST_TOKEN;

  if (useMock) {
    logDiagnostic('MODE', 'Mock-Data Mode Active (VITE_USE_MOCK=true)');
    return { status: 'mock' };
  } else {
    logDiagnostic('MODE', 'Real-Data Mode Active (VITE_USE_MOCK=false)');
  }

  logDiagnostic('CHECK', `Pinging Aggregator: ${apiUrl}`);
  logDiagnostic('AUTH', `Authorization Header: ${hasToken ? 'Present' : 'MISSING'}`);

  if (!import.meta.env.VITE_GRAPH_API_URL) {
    logDiagnostic('CONFIG', 'No API URL found, defaulting to MOCK mode.');
    return { status: 'mock' };
  }

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
    
    let errorMsg = `HTTP Error ${response.status}`;
    if (response.status === 401 || response.status === 403) {
      errorMsg = '🚫 التوكن غير صالح';
      logDiagnostic('ERROR', `Status: ${response.status} | Message: ${errorMsg}`);
      return { status: 'unauthorized', message: errorMsg };
    }
    if (response.status === 404) {
      errorMsg = '⚠️ الرابط غير صحيح (404)';
      logDiagnostic('ERROR', `Status: ${response.status} | Message: ${errorMsg}`);
      return { status: 'not_found', message: errorMsg };
    }
    
    errorMsg = `⚠️ خطأ في الخادم (${response.status})`;
    logDiagnostic('ERROR', `Status: ${response.status} | Message: ${errorMsg}`);
    return { status: 'unreachable', message: errorMsg };
  } catch (error: any) {
    const errorMsg = error.message || 'Unknown Network Error';
    logDiagnostic('ERROR', `Status: Network | Message: ${errorMsg}`);
    
    // Check for specific CORS error string
    if (error instanceof TypeError && error.message.includes('Failed to fetch')) {
      logDiagnostic('ERROR', '[ALERT] CORS Policy mismatch detected. Check Aggregator allowed origins.');
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
    const useMock = import.meta.env.VITE_USE_MOCK === 'true';
    if (!GRAPH_API_URL || forceMock || forceMockOverride || useMock) {
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
