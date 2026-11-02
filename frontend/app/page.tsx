"use client";

import React, { useState, useEffect, useCallback } from "react";
import { Header } from "@/components/Header";
import { ControlConsole } from "@/components/ControlConsole";
import { ShortlistFeed } from "@/components/ShortlistFeed";
import { AgentTerminal, LogEntry } from "@/components/AgentTerminal";
import { TradeCards } from "@/components/TradeCards";
import { ToastContainer, ToastItem } from "@/components/Toast";
import { ProviderConfig, ShortlistItem, TradeCard, StreamEvent } from "@/lib/types";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

export default function Home() {
  const [providers, setProviders] = useState<Record<string, ProviderConfig>>({});
  const [selectedProvider, setSelectedProvider] = useState<string>("google");
  const [selectedModel, setSelectedModel] = useState<string>("gemini-3.8-flash");
  const [apiKey, setApiKey] = useState<string>("");
  const [isHeaded, setIsHeaded] = useState<boolean>(false);

  const [pipelineStatus, setPipelineStatus] = useState<"idle" | "running" | "completed" | "error">("idle");
  const [statusMessage, setStatusMessage] = useState<string>("System Ready");
  const [currentStepText, setCurrentStepText] = useState<string>("Idle");

  const [shortlist, setShortlist] = useState<ShortlistItem[]>([]);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [cards, setCards] = useState<TradeCard[]>([]);
  const [rawOutput, setRawOutput] = useState<string>("");

  const [isVerifying, setIsVerifying] = useState<boolean>(false);
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const addToast = useCallback((message: string, type: "success" | "error" | "info" = "info") => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, message, type }]);
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const addLog = useCallback((text: string, type: LogEntry["type"] = "normal") => {
    const timestamp = new Date().toLocaleTimeString("en-US", { hour12: false });
    const id = Math.random().toString(36).substring(2, 9);
    setLogs((prev) => [...prev, { id, timestamp, text, type }]);
  }, []);

  // Fetch Providers on Load
  useEffect(() => {
    async function fetchModels() {
      try {
        const res = await fetch(`${API_BASE}/api/models`);
        const data = await res.json();
        if (data.providers) {
          setProviders(data.providers);
          const initialP = data.providers["google"] ? "google" : Object.keys(data.providers)[0];
          setSelectedProvider(initialP);
          setSelectedModel(data.providers[initialP]?.default_model || "gemini-3.8-flash");

          // Load key from localStorage
          const savedKey = localStorage.getItem(`crypto_screener_key_${initialP}`) || "";
          setApiKey(savedKey);
        }
      } catch (err: any) {
        addToast(`Failed to connect to backend (${API_BASE}). Ensure 'python app.py' is running.`, "error");
      }
    }
    fetchModels();
  }, [addToast]);

  // Handle Provider Change
  const handleSelectProvider = (pKey: string) => {
    setSelectedProvider(pKey);
    const cfg = providers[pKey];
    if (cfg) {
      setSelectedModel(cfg.default_model);
      const savedKey = localStorage.getItem(`crypto_screener_key_${pKey}`) || "";
      setApiKey(savedKey);
    }
  };

  // Handle API Key Change & Persist
  const handleChangeApiKey = (val: string) => {
    setApiKey(val);
    localStorage.setItem(`crypto_screener_key_${selectedProvider}`, val.trim());
  };

  // Clear Saved Key
  const handleClearKey = () => {
    setApiKey("");
    localStorage.removeItem(`crypto_screener_key_${selectedProvider}`);
    addToast(`Cleared saved API key for ${selectedProvider.toUpperCase()}`, "info");
  };

  // Verify Key Handler
  const handleVerifyKey = async () => {
    if (!apiKey) {
      addToast("Please enter an API Key to verify", "error");
      return;
    }

    setIsVerifying(true);
    try {
      const res = await fetch(`${API_BASE}/api/verify-model`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: selectedProvider,
          model: selectedModel,
          api_key: apiKey
        })
      });
      const data = await res.json();
      if (data.success) {
        addToast(`Verification Success! Connected to ${selectedProvider.toUpperCase()}`, "success");
      } else {
        addToast(`Verification Failed: ${data.error || "Unknown error"}`, "error");
      }
    } catch (err: any) {
      addToast(`Error: ${err.message}`, "error");
    } finally {
      setIsVerifying(false);
    }
  };

  // Start Screening Pipeline
  const handleStartScreening = async () => {
    if (!selectedModel) {
      addToast("Please select a model first", "error");
      return;
    }

    setPipelineStatus("running");
    setStatusMessage("Stage 1: Pre-Screening...");
    setCurrentStepText("Initializing");
    addLog(`Pipeline initialized with ${selectedProvider.toUpperCase()} (${selectedModel}). Mode: ${isHeaded ? "Headed (Watch)" : "Headless"}`, "step");

    try {
      const res = await fetch(`${API_BASE}/api/screen`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          provider: selectedProvider,
          model: selectedModel,
          api_key: apiKey,
          headed: isHeaded
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      const taskId = data.task_id;
      addLog(`Screening Task started (ID: ${taskId}). Listening to live stream...`, "normal");

      // Connect SSE Stream
      const eventSource = new EventSource(`${API_BASE}/api/stream/${taskId}`);

      eventSource.onmessage = (e) => {
        if (!e.data || e.data === ": ping") return;
        try {
          const event: StreamEvent = JSON.parse(e.data);
          handleStreamEvent(event, eventSource);
        } catch (parseErr) {
          console.error("Failed to parse SSE payload", parseErr);
        }
      };

      eventSource.onerror = (e) => {
        console.error("SSE stream error", e);
      };

    } catch (err: any) {
      setPipelineStatus("error");
      setStatusMessage("Failed to start pipeline");
      addLog(`Launch Error: ${err.message}`, "error");
      addToast(`Failed to launch screener: ${err.message}`, "error");
    }
  };

  const handleStreamEvent = (event: StreamEvent, eventSource: EventSource) => {
    if (event.type === "status") {
      setStatusMessage(event.message || "Working...");
      addLog(event.message || "", "normal");
      if (event.stage === "ai_verification") {
        setCurrentStepText("AI Vision Active");
      }
    } else if (event.type === "shortlist") {
      const candidates = event.data || [];
      setShortlist(candidates);
      addLog(`Shortlist compiled: ${candidates.length} coins passing volatility compression.`, "step");
      addToast(`Stage 1 Complete: ${candidates.length} candidate coins shortlisted!`, "success");
    } else if (event.type === "agent_step") {
      setCurrentStepText(`Step ${event.step}`);
      addLog(`[Step ${event.step}] ${event.goal || "Executing action"}`, "step");
      if (event.action) {
        addLog(`↳ ${event.action}`, "action");
      }
    } else if (event.type === "done") {
      setCards(event.cards || []);
      setRawOutput(event.raw_output || "");
      setPipelineStatus("completed");
      setStatusMessage("Verification Completed");
      setCurrentStepText("Done");
      addLog(`Screening finished! Identified ${event.cards?.length || 0} top setups.`, "step");
      addToast("Screening and AI Verification complete!", "success");
      eventSource.close();
    } else if (event.type === "error") {
      setPipelineStatus("error");
      setStatusMessage("Pipeline Error");
      addLog(`ERROR: ${event.message}`, "error");
      addToast(`Pipeline Error: ${event.message}`, "error");
      eventSource.close();
    }
  };

  return (
    <div className="min-h-screen flex flex-col bg-obsidian-950 text-gray-200">
      <Header status={pipelineStatus} statusMessage={statusMessage} />

      <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6 space-y-6">
        {/* CONTROL CONSOLE */}
        <ControlConsole
          providers={providers}
          selectedProvider={selectedProvider}
          onSelectProvider={handleSelectProvider}
          selectedModel={selectedModel}
          onSelectModel={setSelectedModel}
          apiKey={apiKey}
          onChangeApiKey={handleChangeApiKey}
          onClearKey={handleClearKey}
          isHeaded={isHeaded}
          onToggleHeaded={setIsHeaded}
          onStart={handleStartScreening}
          isRunning={pipelineStatus === "running"}
          onVerifyKey={handleVerifyKey}
          isVerifying={isVerifying}
        />

        {/* TWO COLUMN GRID: SHORTLIST + AGENT TERMINAL */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
          <div className="lg:col-span-5">
            <ShortlistFeed items={shortlist} />
          </div>
          <div className="lg:col-span-7">
            <AgentTerminal
              logs={logs}
              currentStep={currentStepText}
              onClear={() => setLogs([])}
              isRunning={pipelineStatus === "running"}
            />
          </div>
        </div>

        {/* VERIFIED TRADING CARDS */}
        <TradeCards
          cards={cards}
          rawOutput={rawOutput}
          onCopySuccess={() => addToast("Raw analysis copied to clipboard!", "success")}
        />
      </main>

      {/* TOAST CONTAINER */}
      <ToastContainer toasts={toasts} onDismiss={removeToast} />
    </div>
  );
}
