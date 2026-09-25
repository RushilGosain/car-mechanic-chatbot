"use client";

import { useRef } from "react";

const ACCEPT = {
  image: "image/*",
  audio: "audio/*",
  video: "video/*",
};

export default function AttachmentControls({ onFilePicked, disabled }) {
  const imageRef = useRef(null);
  const audioRef = useRef(null);
  const videoRef = useRef(null);

  const handleChange = (mediaType) => (e) => {
    const file = e.target.files?.[0];
    if (file) onFilePicked(mediaType, file);
    e.target.value = "";
  };

  return (
    <>
      <input ref={imageRef} type="file" accept={ACCEPT.image} hidden onChange={handleChange("image")} />
      <input ref={audioRef} type="file" accept={ACCEPT.audio} hidden onChange={handleChange("audio")} />
      <input ref={videoRef} type="file" accept={ACCEPT.video} hidden onChange={handleChange("video")} />

      <button
        type="button"
        className="icon-button"
        title="Attach photo"
        disabled={disabled}
        onClick={() => imageRef.current?.click()}
      >
        {/* camera icon */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <path d="M4 8h3l2-2h6l2 2h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1Z" />
          <circle cx="12" cy="14" r="3.2" />
        </svg>
      </button>

      <button
        type="button"
        className="icon-button"
        title="Attach audio"
        disabled={disabled}
        onClick={() => audioRef.current?.click()}
      >
        {/* mic icon */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <rect x="9" y="3" width="6" height="11" rx="3" />
          <path d="M5 11a7 7 0 0 0 14 0M12 18v3" />
        </svg>
      </button>

      <button
        type="button"
        className="icon-button"
        title="Attach video"
        disabled={disabled}
        onClick={() => videoRef.current?.click()}
      >
        {/* video icon */}
        <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8">
          <rect x="3" y="6" width="12" height="12" rx="2" />
          <path d="M15 10l6-3v10l-6-3" />
        </svg>
      </button>
    </>
  );
}
