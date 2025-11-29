"use client";

import React, { JSX } from "react";

type Props = { content: string };

type Block =
  | { type: "heading"; level: number; text: string }
  | { type: "paragraph"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "code"; text: string };

function escapeHtml(s: string): string {
  return s.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
}

function parseBlocks(md: string): Block[] {
  const lines = md.replace(/\r\n?/g, "\n").split("\n");
  const blocks: Block[] = [];
  let i = 0;
  let inCode = false;
  let codeLines: string[] = [];
  let listType: "ul" | "ol" | null = null;
  let listItems: string[] = [];
  let para: string[] = [];

  function flushPara() {
    if (para.length) {
      blocks.push({ type: "paragraph", text: para.join("\n") });
      para = [];
    }
  }
  function flushList() {
    if (listType && listItems.length) {
      blocks.push({ type: listType, items: listItems.slice() } as Block);
    }
    listType = null;
    listItems = [];
  }
  function flushCode() {
    if (codeLines.length) {
      blocks.push({ type: "code", text: codeLines.join("\n") });
      codeLines = [];
    }
  }

  while (i < lines.length) {
    const line = lines[i];
    // Fenced code blocks ```
    if (line.trim().startsWith("```") && !inCode) {
      inCode = true;
      flushPara();
      flushList();
      i++;
      continue;
    }
    if (line.trim().startsWith("```") && inCode) {
      inCode = false;
      flushCode();
      i++;
      continue;
    }
    if (inCode) {
      codeLines.push(line);
      i++;
      continue;
    }

    // Headings #, ##, ###
    const h = /^(#{1,6})\s+(.*)$/.exec(line);
    if (h) {
      flushPara();
      flushList();
      const level = Math.min(6, h[1].length);
      blocks.push({ type: "heading", level, text: h[2] });
      i++;
      continue;
    }

    // Ordered list
    const ol = /^\s*(\d+)\.\s+(.*)$/.exec(line);
    if (ol) {
      flushPara();
      if (listType === "ul") flushList();
      listType = "ol";
      listItems.push(ol[2]);
      i++;
      // Lookahead to gather consecutive list lines
      while (i < lines.length) {
        const l2 = lines[i];
        const m2 = /^\s*\d+\.\s+(.*)$/.exec(l2);
        if (m2) {
          listItems.push(m2[1]);
          i++;
        } else if (l2.trim() === "") {
          i++;
          break;
        } else {
          break;
        }
      }
      flushList();
      continue;
    }

    // Unordered list
    const ul = /^\s*[-*•]\s+(.*)$/.exec(line);
    if (ul) {
      flushPara();
      if (listType === "ol") flushList();
      listType = "ul";
      listItems.push(ul[1]);
      i++;
      // Gather consecutive list lines
      while (i < lines.length) {
        const l2 = lines[i];
        const m2 = /^\s*[-*•]\s+(.*)$/.exec(l2);
        if (m2) {
          listItems.push(m2[1]);
          i++;
        } else if (l2.trim() === "") {
          i++;
          break;
        } else {
          break;
        }
      }
      flushList();
      continue;
    }

    if (line.trim() === "") {
      flushPara();
      i++;
      continue;
    }

    // Paragraph accumulation
    para.push(line);
    i++;
  }

  if (inCode) flushCode();
  flushList();
  flushPara();
  return blocks;
}

function isSafeUrl(href: string): boolean {
  try {
    const u = new URL(href, "http://x");
    const p = u.protocol.toLowerCase();
    return p === "http:" || p === "https:";
  } catch {
    return false;
  }
}

function renderInline(text: string, keyBase: string): React.ReactNode[] {
  // Escape first to avoid accidental HTML
  let safe = escapeHtml(text);

  // Split by inline code `...`
  const parts = safe.split(/`/);
  const out: React.ReactNode[] = [];
  parts.forEach((p, idx) => {
    if (idx % 2 === 1) {
      out.push(
        <code key={`${keyBase}-code-${idx}`}>{p}</code>
      );
    } else {
      // Links [text](url)
      const nodes: React.ReactNode[] = [];
      let lastIndex = 0;
      const linkRe = /\[([^\]]+)\]\(([^)]+)\)/g;
      let m: RegExpExecArray | null;
      while ((m = linkRe.exec(p)) !== null) {
        const before = p.slice(lastIndex, m.index);
        if (before) nodes.push(before);
        const txt = m[1];
        const href = m[2];
        if (isSafeUrl(href)) {
          nodes.push(
            <a key={`${keyBase}-a-${idx}-${m.index}`} href={href} target="_blank" rel="noopener noreferrer">
              {txt}
            </a>
          );
        } else {
          nodes.push(`[${txt}](${href})`);
        }
        lastIndex = m.index + m[0].length;
      }
      const rest = p.slice(lastIndex);
      if (rest) nodes.push(rest);

      // Bold **text** and italic *text*
      const formatted = nodes.map((n, j) => {
        if (typeof n !== "string") return n;
        // Bold
        const bPieces = n.split(/\*\*(.+?)\*\*/g);
        const bNodes: React.ReactNode[] = [];
        bPieces.forEach((bp, bi) => {
          if (bi % 2 === 1) {
            bNodes.push(<strong key={`${keyBase}-b-${idx}-${j}-${bi}`}>{bp}</strong>);
          } else {
            // Italic within non-bold pieces
            const iPieces = bp.split(/\*(.+?)\*/g);
            iPieces.forEach((ip, ii) => {
              if (ii % 2 === 1) {
                bNodes.push(<em key={`${keyBase}-i-${idx}-${j}-${bi}-${ii}`}>{ip}</em>);
              } else if (ip) {
                bNodes.push(ip);
              }
            });
          }
        });
        return <React.Fragment key={`${keyBase}-frag-${idx}-${j}`}>{bNodes}</React.Fragment>;
      });
      out.push(<React.Fragment key={`${keyBase}-text-${idx}`}>{formatted}</React.Fragment>);
    }
  });
  return out;
}

export default function Markdown({ content }: Props) {
  const blocks = React.useMemo(() => parseBlocks(content || ""), [content]);
  return (
    <div className="md">
      {blocks.map((b, i) => {
        switch (b.type) {
          case "heading": {
            const Tag = (`h${Math.max(1, Math.min(6, b.level))}` as unknown) as keyof JSX.IntrinsicElements;
            return <Tag key={i}>{renderInline(b.text, `h-${i}`)}</Tag>;
          }
          case "ul":
            return (
              <ul key={i}>
                {b.items.map((it, j) => (
                  <li key={j}>{renderInline(it, `ul-${i}-${j}`)}</li>
                ))}
              </ul>
            );
          case "ol":
            return (
              <ol key={i}>
                {b.items.map((it, j) => (
                  <li key={j}>{renderInline(it, `ol-${i}-${j}`)}</li>
                ))}
              </ol>
            );
          case "code":
            return (
              <pre key={i}>
                <code>{b.text}</code>
              </pre>
            );
          case "paragraph":
          default: {
            // Preserve single line breaks within paragraph
            const lines = b.text.split("\n");
            return (
              <p key={i}>
                {lines.map((ln, idx) => (
                  <React.Fragment key={idx}>
                    {renderInline(ln, `p-${i}-${idx}`)}
                    {idx < lines.length - 1 ? <br /> : null}
                  </React.Fragment>
                ))}
              </p>
            );
          }
        }
      })}
    </div>
  );
}

