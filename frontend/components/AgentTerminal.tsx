"use client";

import React, { useRef, useEffect } from "react";
import { Terminal, Trash2, Compass } from "lucide-react";

export interface LogEntry {
  id: string;
  timestamp: string;
  text: string;
  type: "normal" | "step" | "action" | "error";
}

interface AgentTerminalProps {
  logs: LogEntry[];
  currentStep: string;
  onClear: () => void;
  isRunning: boolean;
}

export function AgentTerminal({ logs, currentStep, onClear, isRunning }: AgentTerminalProps) {
  const containerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (containerRef.current) {
      containerRef.current.scrollTop = containerRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <section className="bg-obsidian-900 rounded-xl border border-obsidian-750 flex flex-col h-[520px] shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-obsidian-750 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Terminal className="w-4 h-4 text-emerald-400" />
          <h2 className="text-base font-semibold text-white tracking-wide">
            Autonomous Agent Feed
          </h2>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={onClear}
            className="text-xs text-gray-400 hover:text-gray-200 px-2 py-1 rounded bg-obsidian-850 border border-obsidian-750 transition-colors flex items-center space-x-1"
          >
            <Trash2 className="w-3 h-3" />
            <span>Clear</span>
          </button>
          <span className="text-xs font-mono px-2 py-0.5 rounded bg-obsidian-850 border border-obsidian-750 text-gold-metallic">
            {isRunning ? currentStep : "Idle"}
          </span>
        </div>
      </div>

      {/* Terminal Content */}
      <div
        ref={containerRef}
        className="flex-1 overflow-y-auto p-4 font-mono text-xs text-gray-300 space-y-2 bg-obsidian-950/90"
      >
        {logs.length === 0 ? (
          <div className="text-gray-500 italic space-y-1">
            <p>// Autonomous browser-use agent ready.</p>
            <p>// Once Stage 1 finishes, the agent will inspect TradingView 1h/4h charts and Perpetual Futures.</p>
          </div>
        ) : (
          logs.map((log) => {
            const colorClass =
              log.type === "step"
                ? "text-gold-light font-semibold"
                : log.type === "action"
                ? "text-emerald-400"
                : log.type === "error"
                ? "text-red-400 font-semibold"
                : "text-gray-300";

            return (
              <div key={log.id} className={`leading-relaxed ${colorClass}`}>
                <span className="text-gray-500 select-none mr-2">[{log.timestamp}]</span>
                <span>{log.text}</span>
              </div>
            );
          })
        )}
      </div>

      {/* Terminal Footer Status */}
      <div className="px-4 py-2 border-t border-obsidian-750 bg-obsidian-850/80 flex items-center justify-between text-[11px] text-gray-400 font-mono">
        <span className="flex items-center space-x-1.5">
          <Compass className="w-3 h-3 text-gold-accent" />
          <span>Stage 2: TradingView & Perpetual Order Book Verification</span>
        </span>
        <span className="text-gray-500">Live SSE Stream</span>
      </div>
    </section>
  );
}
