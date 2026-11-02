"use client";

import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Cpu, KeyRound, Monitor, Play, Loader2, ShieldCheck, Eye, EyeOff } from "lucide-react";
import { ProviderConfig } from "@/lib/types";

interface ControlConsoleProps {
  providers: Record<string, ProviderConfig>;
  selectedProvider: string;
  onSelectProvider: (provider: string) => void;
  selectedModel: string;
  onSelectModel: (model: string) => void;
  apiKey: string;
  onChangeApiKey: (key: string) => void;
  onClearKey?: () => void;
  isHeaded: boolean;
  onToggleHeaded: (val: boolean) => void;
  onStart: () => void;
  isRunning: boolean;
  onVerifyKey: () => Promise<void>;
  isVerifying: boolean;
}

export function ControlConsole({
  providers,
  selectedProvider,
  onSelectProvider,
  selectedModel,
  onSelectModel,
  apiKey,
  onChangeApiKey,
  onClearKey,
  isHeaded,
  onToggleHeaded,
  onStart,
  isRunning,
  onVerifyKey,
  isVerifying
}: ControlConsoleProps) {
  const [showKey, setShowKey] = useState(false);
  const [isCustomModel, setIsCustomModel] = useState(false);
  const [customModelVal, setCustomModelVal] = useState("");

  const currentProviderConfig = providers[selectedProvider] || null;

  useEffect(() => {
    if (selectedModel && currentProviderConfig) {
      const exists = currentProviderConfig.models.some((m) => m.id === selectedModel);
      if (!exists && selectedModel !== "") {
        setIsCustomModel(true);
        setCustomModelVal(selectedModel);
      } else {
        setIsCustomModel(false);
      }
    }
  }, [selectedModel, currentProviderConfig]);

  const providerKeys = Object.keys(providers);

  return (
    <section className="bg-obsidian-900 rounded-lg border border-obsidian-750 p-4 shadow-sm space-y-3.5">
      {/* 1. PROVIDER SELECTION TABS */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-obsidian-750 pb-3">
        <label className="text-xs font-semibold uppercase tracking-wider text-gray-300 flex items-center space-x-1.5 shrink-0">
          <Cpu className="w-3.5 h-3.5 text-gold-metallic" />
          <span>Select Engine</span>
        </label>

        <div className="flex flex-wrap gap-1 p-0.5 bg-obsidian-950 rounded border border-obsidian-800">
          {providerKeys.map((pKey) => {
            const p = providers[pKey];
            const isSelected = selectedProvider === pKey;

            return (
              <button
                key={pKey}
                onClick={() => onSelectProvider(pKey)}
                className={`relative px-3 py-1 rounded text-xs font-medium transition-colors ${
                  isSelected ? "text-white font-semibold" : "text-gray-400 hover:text-gray-200"
                }`}
              >
                {isSelected && (
                  <motion.div
                    layoutId="active-provider-pill"
                    className="absolute inset-0 bg-obsidian-800 border border-gold-border rounded shadow-sm"
                    transition={{ type: "spring", stiffness: 450, damping: 35 }}
                  />
                )}
                <span className="relative z-10 flex items-center space-x-1.5">
                  {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-gold-metallic" />}
                  <span>{p.name}</span>
                </span>
              </button>
            );
          })}
        </div>
      </div>

      {/* 2. THREE COMPACT COLUMNS */}
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 items-end">
        
        {/* Model Selection */}
        <div className="md:col-span-4 space-y-1.5">
          <label className="text-xs font-medium text-gray-400">
            Model Architecture
          </label>

          <select
            value={isCustomModel ? "__custom__" : selectedModel}
            onChange={(e) => {
              if (e.target.value === "__custom__") {
                setIsCustomModel(true);
              } else {
                setIsCustomModel(false);
                onSelectModel(e.target.value);
              }
            }}
            className="w-full bg-obsidian-850 border border-obsidian-700 rounded px-2.5 py-1.5 text-xs text-gray-200 focus:outline-none focus:border-gold-metallic transition-colors"
          >
            {currentProviderConfig?.models.map((m) => (
              <option key={m.id} value={m.id}>
                {m.label}
              </option>
            ))}
            <option value="__custom__">Custom Model ID...</option>
          </select>

          {/* Custom Model Input */}
          <AnimatePresence>
            {isCustomModel && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: "auto" }}
                exit={{ opacity: 0, height: 0 }}
                className="overflow-hidden pt-1"
              >
                <input
                  type="text"
                  placeholder="Enter model string..."
                  value={customModelVal}
                  onChange={(e) => {
                    setCustomModelVal(e.target.value);
                    onSelectModel(e.target.value);
                  }}
                  className="w-full bg-obsidian-850 border border-obsidian-700 rounded px-2.5 py-1 text-xs text-gray-200 font-mono focus:outline-none focus:border-gold-metallic"
                />
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* API Key Configuration */}
        <div className="md:col-span-5 space-y-1.5">
          <div className="flex items-center justify-between">
            <label className="text-xs font-medium text-gray-400 flex items-center space-x-1">
              <KeyRound className="w-3 h-3 text-gold-metallic" />
              <span>API Key</span>
            </label>
            <div className="flex items-center space-x-3">
              {apiKey && onClearKey && (
                <button
                  type="button"
                  onClick={onClearKey}
                  className="text-xs text-rose-400/80 hover:text-rose-300 transition-colors cursor-pointer"
                  title="Remove saved key from browser"
                >
                  Clear Key
                </button>
              )}
              <button
                type="button"
                onClick={onVerifyKey}
                disabled={isVerifying || !apiKey}
                className="text-xs text-gold-metallic hover:text-gold-400 transition-colors flex items-center space-x-1 disabled:opacity-40 cursor-pointer"
              >
                {isVerifying ? (
                  <Loader2 className="w-3 h-3 animate-spin" />
                ) : (
                  <ShieldCheck className="w-3 h-3" />
                )}
                <span>{isVerifying ? "Verifying..." : "Verify"}</span>
              </button>
            </div>
          </div>

          <div className="relative">
            <input
              type={showKey ? "text" : "password"}
              value={apiKey}
              onChange={(e) => onChangeApiKey(e.target.value)}
              placeholder={`${currentProviderConfig?.key_placeholder || "Enter API Key"} (saved in browser)`}
              className="w-full bg-obsidian-850 border border-obsidian-700 rounded pl-2.5 pr-8 py-1.5 text-xs text-gray-200 font-mono focus:outline-none focus:border-gold-metallic transition-colors"
            />
            <button
              type="button"
              onClick={() => setShowKey(!showKey)}
              className="absolute inset-y-0 right-0 pr-2.5 flex items-center text-gray-400 hover:text-gray-200"
            >
              {showKey ? <EyeOff className="w-3.5 h-3.5" /> : <Eye className="w-3.5 h-3.5" />}
            </button>
          </div>
        </div>

        {/* Mode Toggle & Flat Luxury Launch Button */}
        <div className="md:col-span-3 flex flex-col justify-end space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-400 flex items-center space-x-1">
              <Monitor className="w-3 h-3 text-gold-metallic" />
              <span>Watch Browser:</span>
            </span>

            {/* Spring Switch with explicit justify-start vs justify-end */}
            <button
              type="button"
              onClick={() => onToggleHeaded(!isHeaded)}
              className={`w-10 h-6 rounded-full transition-colors flex items-center p-1 cursor-pointer ${
                isHeaded
                  ? "bg-gold-metallic justify-end"
                  : "bg-obsidian-750 border border-obsidian-700 justify-start"
              }`}
            >
              <motion.div
                layout
                transition={{ type: "spring", stiffness: 500, damping: 30 }}
                className={`w-4 h-4 rounded-full shadow-sm ${
                  isHeaded ? "bg-obsidian-950" : "bg-gray-400"
                }`}
              />
            </button>
          </div>

          {/* Action Launch Button */}
          <motion.button
            whileHover={{ scale: isRunning ? 1 : 1.01 }}
            whileTap={{ scale: isRunning ? 1 : 0.98 }}
            onClick={onStart}
            disabled={isRunning}
            className="w-full py-2 px-3 rounded bg-gold-metallic hover:bg-gold-400 text-obsidian-950 font-bold text-xs tracking-wider transition-colors flex items-center justify-center space-x-1.5 disabled:opacity-50 shadow-sm"
          >
            {isRunning ? (
              <>
                <Loader2 className="w-3.5 h-3.5 animate-spin text-obsidian-950" />
                <span>SCREENING...</span>
              </>
            ) : (
              <>
                <Play className="w-3.5 h-3.5 fill-obsidian-950" />
                <span>LAUNCH SCREENER</span>
              </>
            )}
          </motion.button>
        </div>

      </div>
    </section>
  );
}
