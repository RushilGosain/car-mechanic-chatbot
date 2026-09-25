const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL || "http://127.0.0.1:8000/api";

export async function chatWithMechanic(message) {
  const res = await fetch(`${API_BASE_URL}/chat/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ message }),
  });

  if (!res.ok) {
    throw new Error(`Chat request failed: ${res.status}`);
  }

  return res.json();
}

export async function uploadFile(file) {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/upload/`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    throw new Error(`Upload request failed: ${res.status}`);
  }

  return res.json();
}

export async function getDiagnosis(data) {
  const res = await fetch(`${API_BASE_URL}/diagnosis/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error(`Diagnosis request failed: ${res.status}`);
  }

  return res.json();
}

export async function createBooking(data) {
  const res = await fetch(`${API_BASE_URL}/booking/`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!res.ok) {
    throw new Error(`Booking request failed: ${res.status}`);
  }

  return res.json();
}

export async function getBooking(id) {
  const res = await fetch(`${API_BASE_URL}/booking/${id}/`);

  if (!res.ok) {
    throw new Error(`Booking request failed: ${res.status}`);
  }

  return res.json();
}