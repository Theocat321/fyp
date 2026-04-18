"use client";

import React from "react";
import MessageBubble from "./MessageBubble";

type Msg = { role: "user" | "assistant"; text: string };

interface MessageListProps {
  messages: Msg[];
  busy: boolean;
  listRef: React.RefObject<HTMLDivElement | null>;
  onScroll: () => void;
}

export default function MessageList({ messages, busy, listRef, onScroll }: MessageListProps) {
  return (
    <div className="chat-list" ref={listRef} onScroll={onScroll}>
      {messages.map((m, i) => (
        <MessageBubble key={i} role={m.role} text={m.text} />
      ))}
      {busy && <MessageBubble role="assistant" typing />}
      <div className="sr-only" aria-live="polite" aria-atomic="true">
        {busy ? "VodaCare is typing" : ""}
      </div>
    </div>
  );
}
