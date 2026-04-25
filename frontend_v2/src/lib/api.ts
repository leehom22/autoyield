const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

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
