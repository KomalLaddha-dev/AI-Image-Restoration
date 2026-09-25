const API_BASE = '';  // Uses Vite proxy in dev, same-origin in prod

/**
 * Submit an image for restoration (async).
 */
export async function submitRestore(file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('options', JSON.stringify(options));

  const res = await fetch(`${API_BASE}/api/v1/restore`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error(`Restore failed: ${res.statusText}`);
  return res.json();
}

/**
 * Poll restoration job status.
 */
export async function getRestoreResult(jobId) {
  const res = await fetch(`${API_BASE}/api/v1/restore/${jobId}`);
  if (!res.ok) throw new Error(`Job poll failed: ${res.statusText}`);
  return res.json();
}

/**
 * Synchronous restore — returns image blob directly.
 */
export async function restoreSync(file, options = {}) {
  const formData = new FormData();
  formData.append('file', file);
  formData.append('options', JSON.stringify(options));

  const res = await fetch(`${API_BASE}/api/v1/restore/sync`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error(`Sync restore failed: ${res.statusText}`);

  const blob = await res.blob();
  const processingTime = res.headers.get('X-Processing-Time-Ms');
  const stages = res.headers.get('X-Stages-Applied');

  return {
    blob,
    url: URL.createObjectURL(blob),
    processingTime: parseInt(processingTime || '0'),
    stages: stages ? stages.split(',') : [],
  };
}

/**
 * Identify a monument from an image.
 */
export async function identifyMonument(file) {
  const formData = new FormData();
  formData.append('file', file);

  const res = await fetch(`${API_BASE}/api/v1/identify`, {
    method: 'POST',
    body: formData,
  });

  if (!res.ok) throw new Error(`Identify failed: ${res.statusText}`);
  return res.json();
}

/**
 * Get historical information for a monument.
 */
export async function getHistory(monumentId, query = null) {
  const params = query ? `?query=${encodeURIComponent(query)}` : '';
  const res = await fetch(`${API_BASE}/api/v1/history/${monumentId}${params}`);
  if (!res.ok) throw new Error(`History failed: ${res.statusText}`);
  return res.json();
}

/**
 * Combined: identify + get history in one call.
 */
export async function identifyAndInform(file) {
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
