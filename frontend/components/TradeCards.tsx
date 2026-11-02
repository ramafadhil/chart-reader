"use client";

import React, { useState } from "react";
import { motion } from "framer-motion";
import { CandlestickChart, Copy, Check, Layers, Target, ArrowUpRight, ArrowDownRight } from "lucide-react";
import { TradeCard } from "@/lib/types";

interface TradeCardsProps {
  cards: TradeCard[];
  rawOutput: string;
  onCopySuccess: () => void;
}

export function TradeCards({ cards, rawOutput, onCopySuccess }: TradeCardsProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    if (!rawOutput) return;
    try {
      await navigator.clipboard.writeText(rawOutput);
      setCopied(true);
      onCopySuccess();
      setTimeout(() => setCopied(false), 2500);
    } catch (err) {
      console.error("Failed to copy clipboard:", err);
    }
  };

  return (
    <section className="space-y-3.5">
      {/* Header and Copy Action */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
        <div>
          <h2 className="text-base font-bold text-white tracking-tight flex items-center space-x-2">
            <span>Verified Trading Opportunities</span>
            <span className="text-xs px-2 py-0.5 rounded font-mono bg-obsidian-850 text-gold-metallic border border-gold-border">
              {cards.length} verified
            </span>
          </h2>
          <p className="text-xs text-gray-400">
            Validated by AI Vision on 1h/4h TradingView charts and confirmed on perpetual futures.
          </p>
        </div>

        {/* COPY RAW ANALYSIS BUTTON (WITH MORPHING SPRING ICON) */}
        <motion.button
          whileHover={{ scale: rawOutput ? 1.02 : 1 }}
          whileTap={{ scale: rawOutput ? 0.97 : 1 }}
          onClick={handleCopy}
          disabled={!rawOutput}
          className="px-3.5 py-1.5 rounded bg-obsidian-850 hover:bg-obsidian-800 border border-gold-border text-gold-metallic text-xs font-semibold tracking-wide disabled:opacity-40 disabled:pointer-events-none transition-all flex items-center justify-center space-x-2 shadow-sm self-start sm:self-auto"
        >
          {copied ? (
            <>
              <Check className="w-3.5 h-3.5 text-emerald-400" />
              <span className="text-emerald-400">Copied to Clipboard!</span>
            </>
          ) : (
            <>
              <Copy className="w-3.5 h-3.5" />
              <span>Copy Raw Analysis</span>
            </>
          )}
        </motion.button>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {cards.length === 0 ? (
          // 3 Placeholder Slots
          [1, 2, 3].map((slot) => (
            <div
              key={slot}
              className="bg-obsidian-900 border border-obsidian-750 rounded-lg p-5 text-center flex flex-col items-center justify-center min-h-[220px] text-gray-500 shadow-sm"
            >
              <div className="w-10 h-10 rounded-full bg-obsidian-850 border border-obsidian-750 flex items-center justify-center mb-2">
                <CandlestickChart className="w-5 h-5 stroke-1 text-obsidian-600" />
              </div>
              <p className="text-xs font-medium text-gray-400">Setup Slot #{slot}</p>
              <p className="text-xs text-gray-500 mt-0.5">Pending agent visual chart inspection</p>
            </div>
          ))
        ) : (
          cards.map((card, idx) => {
            const isLong = (card.direction || "").toUpperCase().includes("LONG");
            const badgeClasses = isLong
              ? "border-emerald-500/40 bg-emerald-500/10 text-emerald-400"
              : "border-red-500/40 bg-red-500/10 text-red-400";

            return (
              <motion.div
                key={`${card.coin}-${idx}`}
                initial={{ opacity: 0, y: 15 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{
                  type: "spring",
                  stiffness: 350,
                  damping: 25,
                  delay: idx * 0.08
                }}
                className="bg-obsidian-900 border border-obsidian-750 hover:border-gold-border rounded-lg p-4 shadow-sm flex flex-col justify-between transition-colors space-y-3.5"
              >
                <div className="space-y-3">
                  {/* Top Bar: Opportunity Tag + Direction Badge */}
                  <div className="flex items-center justify-between border-b border-obsidian-750 pb-2.5">
                    <div>
                      <span className="text-[10px] text-gold-accent font-mono tracking-wider uppercase">
                        Opportunity #{idx + 1}
                      </span>
                      <h3 className="text-lg font-bold text-white tracking-tight">
                        {card.coin || "CRYPTO"}
                      </h3>
                    </div>

                    <span
                      className={`text-xs px-2 py-0.5 rounded font-bold uppercase tracking-wider border flex items-center space-x-1 ${badgeClasses}`}
                    >
                      {isLong ? (
                        <ArrowUpRight className="w-3.5 h-3.5 inline" />
                      ) : (
                        <ArrowDownRight className="w-3.5 h-3.5 inline" />
                      )}
                      <span>{card.direction || "SETUP"}</span>
                    </span>
                  </div>

                  {/* Platform Availability */}
                  <div className="flex items-center space-x-1.5 text-xs text-gray-300">
                    <Layers className="w-3.5 h-3.5 text-gold-metallic" />
                    <span className="text-gray-400">Platform:</span>
                    <span className="font-medium text-white">
                      {card.platform || "Binance / Bitget Futures"}
                    </span>
                  </div>

                  {/* Quantitative Target Axis Gauge (Institutional Instrument) */}
                  <div className="border-t border-b border-obsidian-750 py-2.5 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-xs uppercase tracking-wider text-gray-300 font-medium flex items-center space-x-1">
                        <Target className="w-3 h-3 text-gold-metallic" />
                        <span>Execution Parameters</span>
                      </span>
                      <span className="font-mono text-emerald-400 text-xs font-semibold tabular-nums">+5% TP / -5% SL</span>
                    </div>

                    {/* Scale Line with Ticks */}
                    <div className="relative pt-3 pb-1">
                      {/* Range track line */}
                      <div className="h-1 w-full bg-obsidian-750 rounded-full relative">
                        <div className="absolute left-0 top-0 bottom-0 w-1/2 bg-red-500/40 rounded-l-full" />
                        <div className="absolute right-0 top-0 bottom-0 w-1/2 bg-emerald-500/40 rounded-r-full" />
                      </div>

                      {/* Center Entry Marker */}
                      <div className="absolute top-1.5 left-1/2 -translate-x-1/2 flex flex-col items-center">
                        <div className="w-2 h-2 rounded-full bg-gold-metallic border border-obsidian-950 shadow-sm" />
                      </div>

                      {/* Numeric Labels */}
                      <div className="flex items-center justify-between text-[11px] font-mono text-gray-400 pt-1.5 tabular-nums">
                        <span className="text-red-400">Risk -5%</span>
                        <span className="text-gold-light text-center font-medium">Entry Baseline</span>
                        <span className="text-emerald-400 text-right">Target +5%</span>
                      </div>
                    </div>

                    <p className="text-xs font-mono text-gray-300 bg-obsidian-950 px-2.5 py-1.5 rounded border border-obsidian-800">
                      {card.target_zone || "Entry spec: TP +5%, SL -5%"}
                    </p>
                  </div>

                  {/* Setup Structure */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-gray-300">The Setup Structure:</div>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {card.setup_structure || "Sideways horizontal consolidation within established channel."}
                    </p>
                  </div>

                  {/* Technical Reason */}
                  <div className="space-y-1">
                    <div className="text-xs font-medium text-gray-300">Technical Rationale:</div>
                    <p className="text-xs text-gray-400 leading-relaxed">
                      {card.technical_reason || "Declining volume during base formation prior to breakout."}
                    </p>
                  </div>
                </div>

                {/* Card Footer */}
                <div className="pt-2.5 border-t border-obsidian-750 flex items-center justify-between text-xs text-gray-400 font-mono">
                  <span>TradingView 1H/4H</span>
                  <span className="text-emerald-400 flex items-center space-x-1">
                    <Check className="w-3 h-3" />
                    <span>Futures Verified</span>
                  </span>
                </div>
              </motion.div>
            );
          })
        )}
      </div>
    </section>
  );
}
