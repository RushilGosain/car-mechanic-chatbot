"use client";

import { useState } from "react";

export default function BookingModal({ onClose, onSubmit, submitting, result }) {
  const [customerName, setCustomerName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [preferredDate, setPreferredDate] = useState("");
  const [notes, setNotes] = useState("");

  const canSubmit = customerName.trim() && phoneNumber.trim();

  return (
    <div className="modal-backdrop" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h2>Book a mechanic</h2>

        {result ? (
          <div className="booking-confirm">
            Booking #{result.id} confirmed — status: {result.status}. A mechanic will reach out on{" "}
            {result.phone_number}.
          </div>
        ) : (
          <>
            <div className="field">
              <label>Your name</label>
              <input value={customerName} onChange={(e) => setCustomerName(e.target.value)} placeholder="Rushil Sharma" />
            </div>
            <div className="field">
              <label>Phone number</label>
              <input value={phoneNumber} onChange={(e) => setPhoneNumber(e.target.value)} placeholder="98XXXXXXXX" />
            </div>
            <div className="field">
              <label>Preferred date (optional)</label>
              <input type="date" value={preferredDate} onChange={(e) => setPreferredDate(e.target.value)} />
            </div>
            <div className="field">
              <label>Notes (optional)</label>
              <input value={notes} onChange={(e) => setNotes(e.target.value)} placeholder="Prefer morning slot" />
            </div>
            <div className="modal-actions">
              <button className="cta-button secondary" onClick={onClose}>
                Cancel
              </button>
              <button
                className="cta-button"
                disabled={!canSubmit || submitting}
                onClick={() => onSubmit({ customerName, phoneNumber, preferredDate, notes })}
              >
                {submitting ? "Booking…" : "Confirm booking"}
              </button>
            </div>
          </>
        )}

        {result && (
          <div className="modal-actions">
            <button className="cta-button" onClick={onClose}>
              Done
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
