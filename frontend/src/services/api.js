const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000';

export async function askAIChat(query, sessionId = null, vehicleId = null, conversationHistory = []) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query,
        session_id: sessionId,
        vehicle_id: vehicleId,
        conversation_history: conversationHistory,
      })
    });
    if (!res.ok) throw new Error(`Chat API Error: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error('askAIChat error:', err);
    throw err;
  }
}

export async function compareCars(carA, carB) {
  try {
    const res = await fetch(`${API_BASE_URL}/api/compare/cars`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ car_a: carA, car_b: carB })
    });
    if (!res.ok) throw new Error(`Compare API Error: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error('compareCars error:', err);
    throw err;
  }
}

async function throwDocumentApiError(res, fallback) {
  const body = await res.json().catch(() => ({}));
  const error = new Error(body.detail || `${fallback} (${res.status}).`);
  error.status = res.status;
  throw error;
}

export async function loginAdmin(username, password) {
  const res = await fetch(`${API_BASE_URL}/api/documents/auth/login`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) await throwDocumentApiError(res, 'Administrator sign-in failed');
  return await res.json();
}

export async function logoutAdmin(adminToken) {
  const res = await fetch(`${API_BASE_URL}/api/documents/auth/logout`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  if (!res.ok) await throwDocumentApiError(res, 'Administrator sign-out failed');
  return await res.json();
}

export async function getDocuments(adminToken) {
  const res = await fetch(`${API_BASE_URL}/api/documents`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  if (!res.ok) await throwDocumentApiError(res, 'Could not load brochures');
  return await res.json();
}

export async function uploadBrochure(file, adminToken) {
  const formData = new FormData();
  formData.append('file', file);
  const res = await fetch(`${API_BASE_URL}/api/documents/upload`, {
    method: 'POST',
    headers: { Authorization: `Bearer ${adminToken}` },
    body: formData,
  });
  if (!res.ok) await throwDocumentApiError(res, 'Upload failed');
  return await res.json();
}

export async function deleteBrochure(documentId, adminToken) {
  const res = await fetch(`${API_BASE_URL}/api/documents/${encodeURIComponent(documentId)}`, {
    method: 'DELETE',
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  if (!res.ok) await throwDocumentApiError(res, 'Could not remove brochure');
  return await res.json();
}

export async function getBrochurePdf(documentId, adminToken) {
  const res = await fetch(`${API_BASE_URL}/api/documents/${encodeURIComponent(documentId)}/file`, {
    headers: { Authorization: `Bearer ${adminToken}` },
  });
  if (!res.ok) await throwDocumentApiError(res, 'Could not open brochure');
  return await res.blob();
}

export async function getVehicles() {
  try {
    const res = await fetch(`${API_BASE_URL}/api/vehicles`);
    if (!res.ok) throw new Error(`Vehicles API Error: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    console.error('getVehicles error:', err);
    return { vehicles: [], total: 0 };
  }
}
