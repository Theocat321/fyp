type Props = {
  role: "user" | "assistant";
  text?: string;
  typing?: boolean;
};

export default function MessageBubble({ role, text = "", typing = false }: Props) {
  const isUser = role === "user";
  const displayText = typing ? "" : (isUser ? text : text.replace(/\*/g, ""));
  return (
    <div className={`bubble-row ${isUser ? "right" : "left"}`}>
      <div className={`bubble ${isUser ? "user" : "assistant"}`}>
        {typing ? (
          <div className="typing-dots" aria-label="Assistant is typing">
            <span />
            <span />
            <span />
          </div>
        ) : (
          displayText
        )}
      </div>
    </div>
  );
}
