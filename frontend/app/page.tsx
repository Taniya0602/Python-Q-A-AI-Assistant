"use client";

import { useEffect, useRef, useState } from "react";
import { Send, Code2, Zap, Database, RefreshCw } from "lucide-react";
import { ChatMessage, HealthResponse } from "@/types/api";
import MarkdownAnswer from "@/components/MarkdownAnswer";
import SourceCards from "@/components/SourceCard";
import LoadingDots from "@/components/LoadingDots";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const EXAMPLE_QUESTIONS = [
  "How do I reverse a list in Python?",
  "What is a list comprehension?",
  "How do decorators work in Python?",
  "What's the difference between a list and a tuple?",
  "How do I handle exceptions in Python?",
  "How do I use async/await?",
];

function genId() {
  return Math.random().toString(36).slice(2);
}

export default function Home() {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    fetch(`${API}/health`)
      .then((r) => r.json())
      .then(setHealth)
      .catch(() => setHealth(null));
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, loading]);

  const sendQuestion = async (question: string) => {
    if (!question.trim() || loading) return;
    setError(null);

    const userMsg: ChatMessage = {
      id: genId(),
      role: "user",
      content: question.trim(),
      timestamp: new Date(),
    };
    setMessages((prev) => [...prev, userMsg]);
    setInput("");
    setLoading(true);

    try {
      const res = await fetch(`${API}/ask`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ question: question.trim() }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `HTTP ${res.status}`);
      }

      const data = await res.json();
      const assistantMsg: ChatMessage = {
        id: genId(),
        role: "assistant",
        content: data.answer,
        sources: data.sources,
        latency_ms: data.latency_ms,
        model: data.model,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, assistantMsg]);
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : "Unknown error";
      setError(msg);
    } finally {
      setLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    sendQuestion(input);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendQuestion(input);
    }
  };

  const clearChat = () => {
    setMessages([]);
    setError(null);
  };

  return (
    <div className="flex flex-col h-screen bg-[#0d0f14]">
      {/* Header */}
      <header className="shrink-0 border-b border-slate-800 bg-[#0d0f14]/95 backdrop-blur sticky top-0 z-10">
        <div className="max-w-4xl mx-auto px-4 h-14 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 bg-gradient-to-br from-sky-500 to-blue-600 rounded-lg flex items-center justify-center">
              <Code2 size={16} className="text-white" />
            </div>
            <div>
              <h1 className="text-sm font-semibold text-white leading-tight">Python Q&A Assistant</h1>
              <p className="text-[10px] text-slate-500 leading-tight">Grounded in Stack Overflow · Powered by Gemini</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {health && (
              <div className="flex items-center gap-2 text-xs">
                <span
                  className={`w-2 h-2 rounded-full ${
                    health.status === "healthy" ? "bg-emerald-400 shadow-emerald-400/50 shadow-sm" : "bg-yellow-400"
                  }`}
                />
                <span className="text-slate-400 hidden sm:inline">
                  {health.total_documents.toLocaleString()} docs
                </span>
                <span className="text-slate-600">·</span>
                <Database size={12} className="text-slate-500" />
                <span className="text-slate-500 hidden sm:inline font-mono text-[10px]">{health.model}</span>
              </div>
            )}
            {messages.length > 0 && (
              <button
                onClick={clearChat}
                className="text-slate-500 hover:text-slate-300 transition-colors p-1"
                title="Clear chat"
              >
                <RefreshCw size={14} />
              </button>
            )}
          </div>
        </div>
      </header>

      {/* Messages */}
      <main className="flex-1 overflow-y-auto">
        <div className="max-w-4xl mx-auto px-4 py-6">
          {messages.length === 0 ? (
            /* Empty state */
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center">
              <div className="w-16 h-16 bg-gradient-to-br from-sky-500/20 to-blue-600/20 border border-sky-500/30 rounded-2xl flex items-center justify-center mb-5">
                <Code2 size={28} className="text-sky-400" />
              </div>
              <h2 className="text-xl font-semibold text-white mb-2">Ask me anything about Python</h2>
              <p className="text-slate-500 text-sm max-w-md mb-8">
                Answers are grounded strictly in Stack Overflow data — no hallucinations.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-lg">
                {EXAMPLE_QUESTIONS.map((q) => (
                  <button
                    key={q}
                    onClick={() => sendQuestion(q)}
                    className="text-left text-xs text-slate-400 bg-slate-800/60 hover:bg-slate-800 border border-slate-700/60 hover:border-slate-600 rounded-lg px-3 py-2.5 transition-all"
                  >
                    {q}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={`flex gap-3 ${msg.role === "user" ? "justify-end" : "justify-start"}`}
                >
                  {msg.role === "assistant" && (
                    <div className="shrink-0 w-7 h-7 mt-0.5 bg-gradient-to-br from-sky-500 to-blue-600 rounded-lg flex items-center justify-center">
                      <Code2 size={13} className="text-white" />
                    </div>
                  )}

                  <div className={`max-w-[85%] ${msg.role === "user" ? "order-1" : ""}`}>
                    {msg.role === "user" ? (
                      <div className="bg-sky-600 text-white rounded-2xl rounded-tr-sm px-4 py-2.5 text-sm">
                        {msg.content}
                      </div>
                    ) : (
                      <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-sm px-4 py-3">
                        <MarkdownAnswer content={msg.content} />
                        {msg.sources && <SourceCards sources={msg.sources} />}
                        {msg.latency_ms && (
                          <div className="flex items-center gap-3 mt-2.5 pt-2.5 border-t border-slate-700/40">
                            <span className="flex items-center gap-1 text-[10px] text-slate-600">
                              <Zap size={9} />
                              {msg.latency_ms.toFixed(0)}ms
                            </span>
                            {msg.model && (
                              <span className="text-[10px] text-slate-600 font-mono">{msg.model}</span>
                            )}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}

              {loading && (
                <div className="flex gap-3 justify-start">
                  <div className="shrink-0 w-7 h-7 mt-0.5 bg-gradient-to-br from-sky-500 to-blue-600 rounded-lg flex items-center justify-center">
                    <Code2 size={13} className="text-white" />
                  </div>
                  <div className="bg-slate-800/80 border border-slate-700/60 rounded-2xl rounded-tl-sm px-4 py-3">
                    <LoadingDots />
                  </div>
                </div>
              )}

              {error && (
                <div className="flex justify-center">
                  <div className="bg-red-950/60 border border-red-800/60 text-red-400 text-xs rounded-xl px-4 py-2.5 max-w-md">
                    ⚠ {error}
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </main>

      {/* Input */}
      <div className="shrink-0 border-t border-slate-800 bg-[#0d0f14]/95 backdrop-blur">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <form onSubmit={handleSubmit} className="flex gap-2 items-end">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a Python question… (Enter to send, Shift+Enter for newline)"
              rows={1}
              className="flex-1 resize-none bg-slate-800 border border-slate-700 hover:border-slate-600 focus:border-sky-500 focus:outline-none rounded-xl px-4 py-3 text-sm text-white placeholder-slate-500 transition-colors min-h-[46px] max-h-32 overflow-y-auto"
              style={{ height: "auto" }}
              onInput={(e) => {
                const t = e.target as HTMLTextAreaElement;
                t.style.height = "auto";
                t.style.height = Math.min(t.scrollHeight, 128) + "px";
              }}
            />
            <button
              type="submit"
              disabled={!input.trim() || loading}
              className="shrink-0 w-11 h-11 bg-sky-600 hover:bg-sky-500 disabled:bg-slate-700 disabled:cursor-not-allowed text-white rounded-xl flex items-center justify-center transition-colors"
            >
              <Send size={16} />
            </button>
          </form>
          <p className="text-center text-[10px] text-slate-600 mt-2">
            Answers are grounded in Stack Overflow data · Analytics Vidhya AI Engineer Assessment
          </p>
        </div>
      </div>
    </div>
  );
}
