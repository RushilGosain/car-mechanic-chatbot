"use client";

import { useRef, useState } from "react";
import MessageBubble from "@/components/MessageBubble";
import AttachmentControls from "@/components/AttachmentControls";
import BookingModal from "@/components/BookingModal";
import { sendChatMessage, uploadMedia, requestDiagnosis, createBooking } from "@/lib/api";

function timeLabel(date) {
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export default function Home() {
  const [conversationId, setConversationId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [busy, setBusy] = useState(false);
  const [readyForDiagnosis, setReadyForDiagnosis] = useState(false);
  const [diagnosis, setDiagnosis] = useState(null);
  const [bookingOpen, setBookingOpen] = useState(false);
  const [bookingSubmitting, setBookingSubmitting] = useState(false);
  const [bookingResult, setBookingResult] = useState(null);
  const streamRef = useRef(null);

  const pushMessage = (sender, text) => {
    setMessages((prev) => [...prev, { sender, text, time: timeLabel(new Date()) }]);
    requestAnimationFrame(() => {
      streamRef.current?.scrollTo({ top: streamRef.current.scrollHeight, behavior: "smooth" });
    });
  };

  const handleSend = async () => {
    const text = input.trim();
    if (!text || busy) return;
    setInput("");
    pushMessage("user", text);
    setBusy(true);
    try {
      const res = await sendChatMessage({ conversationId, message: text });
      setConversationId(res.conversation_id);
      pushMessage("bot", res.bot_reply);
      setReadyForDiagnosis(res.ready_for_diagnosis);
    } catch (err) {
      pushMessage("bot", "Something went wrong reaching the backend. Is the Django server running?");
    } finally {
      setBusy(false);
    }
  };

  const handleFilePicked = async (mediaType, file) => {
    if (!conversationId) {
      pushMessage("bot", "Tell me a bit about the issue first, then attach media.");
      return;
    }
    setBusy(true);
    pushMessage("user", `[Uploading ${mediaType}: ${file.name}]`);
    try {
      const res = await uploadMedia({ conversationId, mediaType, file });
      pushMessage("bot", res.analysis_note);
    } catch (err) {
      pushMessage("bot", "That upload failed. Please try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleDiagnose = async () => {
    if (!conversationId || busy) return;
    setBusy(true);
    try {
      const res = await requestDiagnosis({ conversationId });
      setDiagnosis(res);
      pushMessage(
        "bot",
        `Diagnosis: ${res.summary}\n\nRecommended action: ${res.suggested_repair}\n\nWould you like me to book a mechanic for this?`
      );
      setReadyForDiagnosis(false);
    } catch (err) {
      pushMessage("bot", "Couldn't generate a diagnosis right now — please try again.");
    } finally {
      setBusy(false);
    }
  };

  const handleBookingSubmit = async ({ customerName, phoneNumber, preferredDate, notes }) => {
    setBookingSubmitting(true);
    try {
      const res = await createBooking({ conversationId, customerName, phoneNumber, preferredDate, notes });
      setBookingResult(res);
      pushMessage("bot", `Booking #${res.id} confirmed. A mechanic will contact you shortly.`);
    } catch (err) {
      pushMessage("bot", "Booking failed — please check the details and try again.");
    } finally {
      setBookingSubmitting(false);
    }
  };

  return (
    <div className="app-shell">
      <header className="topbar">
        <svg className="wrench-mark" viewBox="0 0 24 24" fill="none" stroke="#ffb020" strokeWidth="1.6">
          <path d="M14.7 6.3a4 4 0 0 0-5.4 4.9L3 17.5 5.5 20l6.3-6.3a4 4 0 0 0 4.9-5.4l-2.6 2.6-2-.1-.1-2 2.6-2.6Z" />
        </svg>
        <div className="brand">
          <span className="brand-name">Torque</span>
          <span className="brand-tagline">Virtual mechanic chat</span>
        </div>
        <div className="status-pill">
          <span className={`status-dot ${busy ? "busy" : ""}`} />
          {busy ? "working" : "online"}
        </div>
      </header>

      <div className="layout">
        <aside className="sidebar">
          <div className="sidebar-section">
            <h2>Session</h2>
            <div className="readout">{conversationId || "not started"}</div>
          </div>

          <div className="sidebar-section">
            <h2>Diagnosis</h2>
            {diagnosis ? (
              <div className="diagnosis-card">
                <h3>Technician summary</h3>
                <p>{diagnosis.summary}</p>
                <p style={{ color: "var(--text-dim)" }}>{diagnosis.suggested_repair}</p>
                <span className="confidence">confidence: {diagnosis.confidence}</span>
                <button className="cta-button" onClick={() => setBookingOpen(true)}>
                  Book mechanic
                </button>
              </div>
            ) : (
              <p style={{ fontSize: 13, color: "var(--text-dim)" }}>
                Describe the issue in chat. Once enough detail is gathered, a diagnosis will appear here.
              </p>
            )}
            {readyForDiagnosis && !diagnosis && (
              <button className="cta-button" onClick={handleDiagnose} disabled={busy}>
                Get diagnosis
              </button>
            )}
          </div>

          <div className="sidebar-section">
            <h2>How it works</h2>
            <p style={{ fontSize: 13, color: "var(--text-dim)", lineHeight: 1.5 }}>
              Describe your car&apos;s symptoms, attach a photo/audio/video if useful, then request a
              diagnosis and book a mechanic.
            </p>
          </div>
        </aside>

        <section className="chat-panel">
          <div className="message-stream" ref={streamRef}>
            {messages.length === 0 && (
              <div className="empty-state">
                <h1>What&apos;s wrong with your car?</h1>
                <p>Tell me what you&apos;re hearing, seeing, or feeling — I&apos;ll ask a few follow-ups and diagnose it.</p>
              </div>
            )}
            {messages.map((m, i) => (
              <MessageBubble key={i} sender={m.sender} text={m.text} time={m.time} />
            ))}
          </div>

          <div className="composer">
            <div className="composer-row">
              <AttachmentControls onFilePicked={handleFilePicked} disabled={busy} />
              <textarea
                placeholder="Describe the issue…"
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === "Enter" && !e.shiftKey) {
                    e.preventDefault();
                    handleSend();
                  }
                }}
              />
              <button className="send-button" onClick={handleSend} disabled={busy || !input.trim()}>
                Send
              </button>
            </div>
          </div>
        </section>
      </div>

      {bookingOpen && (
        <BookingModal
          onClose={() => {
            setBookingOpen(false);
            setBookingResult(null);
          }}
          onSubmit={handleBookingSubmit}
          submitting={bookingSubmitting}
          result={bookingResult}
        />
      )}
    </div>
  );
}
