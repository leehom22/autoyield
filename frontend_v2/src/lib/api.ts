const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8080';

export async function adjustVelocity(multiplier: number) {
  const res = await fetch(`${API_BASE}/api/sandbox/adjust-velocity`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ order_velocity_multiplier: multiplier })
  });
  return res.json();
}

export async function triggerCrisis(payload: any) {
  const res = await fetch(`${API_BASE}/api/sandbox/trigger-crisis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload)
  });
  return res.json();
}

export async function sendChatMessage(message: string, sessionId?: string) {
  const res = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ message, session_id: sessionId })
  });
  return res.json();
}

export async function uploadInvoice(file: File) {
  const formData = new FormData();
  formData.append('file', file);
  
  const res = await fetch(`${API_BASE}/api/agent/invoice`, {
    method: 'POST',
    body: formData
  });
  return res.json();
}

export async function getPermissions() {
  const res = await fetch(`${API_BASE}/api/permissions/`);
  return res.json();
}

export async function updatePermissions(permissions: any) {
  const res = await fetch(`${API_BASE}/api/permissions/`, {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(permissions)
  });
  return res.json();
}

export async function approveNotification(notificationId: string, approved: boolean, operatorNote: string = '') {
  const res = await fetch(`${API_BASE}/api/notifications/approve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      notification_id: notificationId,
      approved,
      operator_note: operatorNote
    })
  });
  return res.json();
}

// Pause simulation
export async function pauseSimulation() {
  const res = await fetch(`${API_BASE}/api/sandbox/pause`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  return res.json();
}

// Resume simulation
export async function resumeSimulation() {
  const res = await fetch(`${API_BASE}/api/sandbox/resume`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' }
  });
  return res.json();
}

// Full reset (database + simulation clock)
export async function fullReset(adminSecret: string) {
  const res = await fetch(`${API_BASE}/api/admin/full-reset`, {
    method: 'POST',
    headers: {
      'X-Admin-Secret': adminSecret,
      'Content-Type': 'application/json'
    }
  });
  return res.json();
}
