"use client";

import ReactMarkdown from "react-markdown";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { oneDark } from "react-syntax-highlighter/dist/esm/styles/prism";
import { useState } from "react";
import { Check, Copy } from "lucide-react";

interface Props {
  content: string;
}

function CodeBlock({ language, code }: { language: string; code: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(code);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="relative group my-3">
      <div className="flex items-center justify-between bg-slate-800 px-4 py-1.5 rounded-t-lg border border-slate-700">
        <span className="text-xs text-slate-400 font-mono">{language || "code"}</span>
        <button
          onClick={copy}
          className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-white transition-colors"
        >
          {copied ? <Check size={13} className="text-emerald-400" /> : <Copy size={13} />}
          {copied ? "Copied!" : "Copy"}
        </button>
      </div>
      <SyntaxHighlighter
        language={language || "python"}
        style={oneDark}
        customStyle={{
          margin: 0,
          borderRadius: "0 0 0.5rem 0.5rem",
          border: "1px solid #334155",
          borderTop: "none",
          fontSize: "0.825rem",
          lineHeight: "1.6",
        }}
        showLineNumbers={code.split("\n").length > 5}
      >
        {code}
      </SyntaxHighlighter>
    </div>
  );
}

export default function MarkdownAnswer({ content }: Props) {
  return (
    <div className="prose prose-sm max-w-none text-slate-200">
    <ReactMarkdown
      components={{
        code({ className, children, ...props }) {
          const match = /language-(\w+)/.exec(className || "");
          const code = String(children).replace(/\n$/, "");
          const isBlock = code.includes("\n") || match;

          if (isBlock) {
            return <CodeBlock language={match?.[1] || "python"} code={code} />;
          }
          return (
            <code
              className="bg-slate-800 text-sky-300 px-1.5 py-0.5 rounded text-xs font-mono"
              {...props}
            >
              {children}
            </code>
          );
        },
        p: ({ children }) => <p className="text-slate-200 leading-7 mb-3 last:mb-0">{children}</p>,
        ul: ({ children }) => <ul className="list-disc list-inside space-y-1 mb-3 text-slate-200">{children}</ul>,
        ol: ({ children }) => <ol className="list-decimal list-inside space-y-1 mb-3 text-slate-200">{children}</ol>,
        li: ({ children }) => <li className="text-slate-300 ml-2">{children}</li>,
        strong: ({ children }) => <strong className="text-white font-semibold">{children}</strong>,
        h3: ({ children }) => <h3 className="text-white font-semibold text-sm mt-4 mb-2">{children}</h3>,
        blockquote: ({ children }) => (
          <blockquote className="border-l-2 border-sky-500 pl-4 text-slate-400 italic my-3">{children}</blockquote>
        ),
      }}
    >
      {content}
    </ReactMarkdown>
    </div>
  );
}
