"use client";

import type { Message } from "@langchain/langgraph-sdk";
import { useMemo } from "react";

import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

const TOOL_LABELS: Record<string, string> = {
  web_search: "Searching the web",
  web_fetch: "Reading sources",
  image_search: "Searching for images",
  fact_check: "Fact-checking",
  store_data_point: "Storing data",
  get_sourced_data: "Collecting sources",
  rag_search: "Searching documents",
  rag_search_vector: "Searching documents",
  rag_ingest_uploads: "Indexing uploads",
  rag_ingest_uploads_vector: "Indexing uploads",
  extract_structured_data: "Extracting data",
  list_uploaded_data_files: "Listing files",
  bash: "Running command",
  write_file: "Writing file",
  read_file: "Reading file",
  present_files: "Presenting results",
  task: "Delegating subtask",
};

function labelForTool(name: string): string {
  return TOOL_LABELS[name] ?? "Working";
}

interface ProgressEstimate {
  percent: number;
  label: string;
}

function estimateProgress(messages: Message[]): ProgressEstimate {
  if (!messages || messages.length === 0) {
    return { percent: 3, label: "Starting…" };
  }

  let lastHumanIdx = -1;
  for (let i = messages.length - 1; i >= 0; i--) {
    if (messages[i]!.type === "human") {
      lastHumanIdx = i;
      break;
    }
  }

  const recent = lastHumanIdx >= 0 ? messages.slice(lastHumanIdx + 1) : messages;

  if (recent.length === 0) {
    return { percent: 5, label: "Thinking…" };
  }

  let aiCount = 0;
  let toolCallCount = 0;
  let toolResponseCount = 0;
  let latestPendingTool = "";
  let lastAiHasContent = false;
  let lastAiHasToolCalls = false;

  for (const msg of recent) {
    if (msg.type === "ai") {
      aiCount++;
      const calls = (msg as { tool_calls?: { name: string }[] }).tool_calls;
      if (calls && calls.length > 0) {
        toolCallCount += calls.length;
        latestPendingTool = calls[calls.length - 1]!.name;
        lastAiHasToolCalls = true;
        lastAiHasContent = false;
      } else {
        lastAiHasToolCalls = false;
        const content = typeof msg.content === "string" ? msg.content : "";
        lastAiHasContent = content.trim().length > 0;
      }
    } else if (msg.type === "tool") {
      toolResponseCount++;
    }
  }

  let label: string;
  let percent: number;

  const allToolsDone = toolCallCount > 0 && toolResponseCount >= toolCallCount;

  if (lastAiHasContent && !lastAiHasToolCalls && allToolsDone) {
    // Final generation phase — all tools done, now writing the response
    label = "Generating response…";
    percent = 85;
  } else if (toolCallCount === 0 && aiCount > 0) {
    // Thinking only, no tools yet
    label = "Thinking…";
    percent = 10;
  } else {
    // Mid-process: tool calls in flight or between rounds
    // Each completed tool response is progress; use sqrt curve to 80%
    const completedSteps = toolResponseCount;
    percent = Math.min(80, Math.round(20 * Math.sqrt(completedSteps) + 10));
    label = latestPendingTool
      ? `${labelForTool(latestPendingTool)}…`
      : "Working…";
  }

  return { percent: Math.max(3, Math.min(95, percent)), label };
}

export function StreamingIndicator({
  className,
  messages,
  size = "normal",
}: {
  className?: string;
  messages?: Message[];
  size?: "normal" | "sm";
}) {
  const { percent, label } = useMemo(
    () =>
      messages ? estimateProgress(messages) : { percent: 50, label: "" },
    [messages],
  );

  const widthClass = size === "sm" ? "w-24" : "w-48";
  const heightClass = size === "sm" ? "h-1" : "h-1.5";

  if (size === "sm" || !messages) {
    return (
      <div className={cn("flex items-center", className)}>
        <Progress
          className={cn(
            "animate-pulse bg-amber-500/10 [&_[data-slot=progress-indicator]]:bg-amber-500/60",
            widthClass,
            heightClass,
          )}
          value={percent}
        />
      </div>
    );
  }

  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <Progress
        className={cn(
          "bg-amber-500/10 [&_[data-slot=progress-indicator]]:bg-amber-500/60 [&_[data-slot=progress-indicator]]:transition-all [&_[data-slot=progress-indicator]]:duration-700 [&_[data-slot=progress-indicator]]:ease-out",
          widthClass,
          heightClass,
        )}
        value={percent}
      />
      <span className="text-muted-foreground text-xs">{label}</span>
    </div>
  );
}
