"use client";

import React from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Filter, TrendingUp, TrendingDown, Layers } from "lucide-react";
import { ShortlistItem } from "@/lib/types";

interface ShortlistFeedProps {
  items: ShortlistItem[];
}

export function ShortlistFeed({ items }: ShortlistFeedProps) {
  return (
    <section className="bg-obsidian-900 rounded-xl border border-obsidian-750 flex flex-col h-[520px] shadow-sm">
      {/* Header */}
      <div className="p-4 border-b border-obsidian-750 flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <div className="w-2.5 h-2.5 rounded-full bg-gold-metallic" />
          <h2 className="text-base font-semibold text-white tracking-wide">
            Mathematical Shortlist
          </h2>
        </div>
        <span className="text-xs font-mono px-2 py-0.5 rounded bg-obsidian-850 border border-obsidian-750 text-gold-accent font-medium">
          {items.length} coins
        </span>
      </div>

      {/* Subheader Filter Criteria */}
      <div className="px-4 py-2.5 text-xs text-gray-400 border-b border-obsidian-800 bg-obsidian-850/60 flex items-center justify-between">
        <span className="truncate">Ranks 50–200 • Compression &lt; 0.15 • VMC 3–15%</span>
        <span className="text-gold-metallic font-mono text-[11px] shrink-0">Stage 1</span>
      </div>

      {/* List Container */}
      <div className="flex-1 overflow-y-auto p-3 space-y-2">
        <AnimatePresence mode="popLayout">
          {items.length === 0 ? (
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-full flex flex-col items-center justify-center text-center p-6 text-gray-500"
            >
              <div className="w-12 h-12 rounded-full bg-obsidian-850 border border-obsidian-750 flex items-center justify-center mb-3">
                <Filter className="w-6 h-6 text-obsidian-600" />
              </div>
              <p className="text-xs font-medium text-gray-400">No candidates shortlisted yet</p>
              <p className="text-xs text-gray-500 mt-1 max-w-xs">
                Launch the screener to scrape CoinMarketCap and isolate coins in sideways compression.
              </p>
            </motion.div>
          ) : (
            items.map((coin, index) => {
              const isPositive24h = coin.ch24h >= 0;

              return (
                <motion.div
                  key={`${coin.symbol}-${coin.rank}`}
                  initial={{ opacity: 0, y: 15 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{
                    type: "spring",
                    stiffness: 380,
                    damping: 26,
                    delay: Math.min(index * 0.04, 0.4)
                  }}
                  whileHover={{ scale: 1.01 }}
                  className="bg-obsidian-850 border border-obsidian-750 hover:border-gold-border rounded-lg p-3 transition-colors flex items-center justify-between group shadow-sm"
                >
                  {/* Left: Rank, Symbol, Name */}
                  <div className="flex items-center space-x-3">
                    <span className="text-xs font-mono text-gray-500 w-7">#{coin.rank}</span>
                    <div>
                      <div className="flex items-center space-x-1.5">
                        <span className="text-sm font-bold text-white tracking-wide group-hover:text-gold-light transition-colors">
                          {coin.symbol}
                        </span>
                        <span className="text-xs text-gray-400 truncate max-w-[130px]">
                          {coin.name}
                        </span>
                      </div>
                      <div className="text-xs font-mono text-gold-metallic mt-0.5 tabular-nums">
                        {coin.price || "$0.00"}
                      </div>
                    </div>
                  </div>

                  {/* Right: Compression & VMC Ratios */}
                  <div className="text-right font-mono text-xs space-y-0.5">
                    <div className="text-xs text-gray-300">
                      CR: <span className="text-gold-light font-semibold tabular-nums">{coin.compression_ratio.toFixed(3)}</span>
                    </div>
                    <div className="text-[11px] text-gray-400 flex items-center justify-end space-x-1.5">
                      <span>VMC: {(coin.vmc_ratio * 100).toFixed(1)}%</span>
                      <span className="text-gray-600">•</span>
                      <span className={`flex items-center ${isPositive24h ? "text-emerald-400" : "text-red-400"}`}>
                        {isPositive24h ? (
                          <TrendingUp className="w-3 h-3 mr-0.5 inline" />
                        ) : (
                          <TrendingDown className="w-3 h-3 mr-0.5 inline" />
                        )}
                        {isPositive24h ? "+" : ""}
                        {coin.ch24h}%
                      </span>
                    </div>
                  </div>
                </motion.div>
              );
            })
          )}
        </AnimatePresence>
      </div>
    </section>
  );
}
