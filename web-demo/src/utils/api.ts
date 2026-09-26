import type {
  HistoryResponse,
  IdentifyResultData,
  RestoreOptions,
  RestoreResult,
} from '../types';

const API_BASE = ''; // Uses Vite proxy in dev, same-origin in prod

/**
 * Submit an image for restoration (async).
 */
export async function submitRestore(file: File, options: Partial<RestoreOptions> = {}): Promise<{ job_id: string; message: string }> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('options', JSON.stringify(options));

  const res = await fetch(`${API_BASE}/api/v1/restore`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errorText = await res.text().catch(() => res.statusText);
    throw new Error(`Restore failed (${res.status}): ${errorText}`);
  }
  return res.json();
}

/**
 * Poll restoration job status.
 */
export async function getRestoreResult(jobId: string) {
  const res = await fetch(`${API_BASE}/api/v1/restore/${jobId}`);
  if (!res.ok) throw new Error(`Job poll failed: ${res.statusText}`);
  return res.json();
}

/**
 * Synchronous restore — returns image blob directly with processing metadata.
 */
export async function restoreSync(file: File, options: Partial<RestoreOptions> = {}): Promise<RestoreResult> {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('options', JSON.stringify(options));

  const res = await fetch(`${API_BASE}/api/v1/restore/sync`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errBody = await res.text().catch(() => res.statusText);
    throw new Error(`Restoration failed (${res.status}): ${errBody}`);
  }

  const blob = await res.blob();
  const processingTime = res.headers.get('X-Processing-Time-Ms');
  const stages = res.headers.get('X-Stages-Applied');

  return {
    blob,
    url: URL.createObjectURL(blob),
    processingTime: parseInt(processingTime || '0', 10),
    stages: stages ? stages.split(',') : [],
  };
}

/**
 * Identify a monument from an image.
 */
export async function identifyMonument(file: File): Promise<IdentifyResultData> {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/v1/identify`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) {
    const errBody = await res.text().catch(() => res.statusText);
    throw new Error(`Identification failed (${res.status}): ${errBody}`);
  }
  return res.json();
}

/**
 * Get historical information for a monument.
 */
export async function getHistory(monumentId: string, query: string | null = null): Promise<HistoryResponse> {
  const params = query ? `?query=${encodeURIComponent(query)}` : '';
  const res = await fetch(`${API_BASE}/api/v1/history/${monumentId}${params}`);
  if (!res.ok) {
    const errBody = await res.text().catch(() => res.statusText);
    throw new Error(`History lookup failed (${res.status}): ${errBody}`);
  }
  return res.json();
}

/**
 * Combined: identify + get history in one call.
 */
export async function identifyAndInform(file: File) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/v1/identify-and-inform`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error(`Identify-and-inform failed: ${res.statusText}`);
  return res.json();
}

/**
 * Health check.
 */
export async function healthCheck() {
  const res = await fetch(`${API_BASE}/health`);
  return res.json();
}
