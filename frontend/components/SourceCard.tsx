"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Database } from "lucide-react";
import { Source } from "@/types/api";

interface Props {
  sources: Source[];
}

export default function SourceCards({ sources }: Props) {
  const [open, setOpen] = useState(false);

  if (!sources.length) return null;

  return (
    <div className="mt-3">
      <button
        onClick={() => setOpen(!open)}
        className="flex items-center gap-2 text-xs text-slate-400 hover:text-slate-300 transition-colors"
      >
        <Database size={12} />
        <span>{sources.length} Stack Overflow source{sources.length !== 1 ? "s" : ""}</span>
        {open ? <ChevronUp size={12} /> : <ChevronDown size={12} />}
      </button>

      {open && (
        <div className="mt-2 space-y-2">
          {sources.map((s, i) => (
            <div
              key={i}
              className="bg-slate-800/60 border border-slate-700/60 rounded-lg px-3 py-2.5"
            >
              <div className="flex items-start justify-between gap-3 mb-1">
                <span className="text-xs font-medium text-slate-300 leading-tight">{s.title}</span>
                <span className="shrink-0 text-[10px] bg-emerald-900/50 text-emerald-400 border border-emerald-800 px-1.5 py-0.5 rounded-full font-mono">
                  ▲ {s.score}
                </span>
              </div>
              <p className="text-[11px] text-slate-500 leading-relaxed line-clamp-2">{s.snippet}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
