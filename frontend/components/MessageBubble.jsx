export default function MessageBubble({ sender, text, time }) {
  return (
    <div className={`message-row ${sender}`}>
      <div>
        <div className="bubble">{text}</div>
        {time && (
          <div className="bubble-meta" style={{ textAlign: sender === "user" ? "right" : "left" }}>
            {time}
          </div>
        )}
      </div>
    </div>
  );
}
