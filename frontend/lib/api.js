const API_BASE_URL = process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

async function handle(res) {
  if (!res.ok) {
    const body = await res.text();
    throw new Error(`API error ${res.status}: ${body}`);
  }
  return res.json();
}

export async function sendChatMessage({ conversationId, message }) {
  const res = await fetch(`${API_BASE_URL}/chat/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId, message }),
  });
  return handle(res);
}

export async function uploadMedia({ conversationId, mediaType, file }) {
  const formData = new FormData();
  formData.append("conversation_id", conversationId);
  formData.append("media_type", mediaType);
  formData.append("file", file);
  const res = await fetch(`${API_BASE_URL}/upload/`, { method: "POST", body: formData });
  return handle(res);
}

export async function requestDiagnosis({ conversationId }) {
  const res = await fetch(`${API_BASE_URL}/diagnosis/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ conversation_id: conversationId }),
  });
  return handle(res);
}

export async function createBooking({ conversationId, customerName, phoneNumber, preferredDate, notes }) {
  const res = await fetch(`${API_BASE_URL}/booking/`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      conversation_id: conversationId,
      customer_name: customerName,
      phone_number: phoneNumber,
      preferred_date: preferredDate || null,
      notes: notes || "",
    }),
  });
  return handle(res);
}

export async function getBooking(id) {
  const res = await fetch(`${API_BASE_URL}/booking/${id}/`);
  return handle(res);
}
