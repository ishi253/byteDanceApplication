"use client";

import {
  SearchIcon,
  ShieldCheckIcon,
  FileTextIcon,
  MessageSquareIcon,
} from "lucide-react";

import { Section } from "../section";

const STEPS = [
  {
    step: 1,
    icon: MessageSquareIcon,
    title: "Define your question",
    body: "Enter a market, industry, or GTM question. Upload PDFs and industry reports to supplement the research.",
    accent: "from-amber-500/20 to-amber-500/5",
    iconColor: "text-amber-400",
    borderColor: "border-amber-500/10",
  },
  {
    step: 2,
    icon: SearchIcon,
    title: "Multi-source search",
    body: "The agent queries live web data via Tavily and cross-references your uploaded documents through RAG retrieval.",
    accent: "from-teal-500/20 to-teal-500/5",
    iconColor: "text-teal-400",
    borderColor: "border-teal-500/10",
  },
  {
    step: 3,
    icon: ShieldCheckIcon,
    title: "Validate & score",
    body: "Every claim is cross-checked across sources and assigned a confidence level: High (3+), Medium (2), or Low (1).",
    accent: "from-purple-500/20 to-purple-500/5",
    iconColor: "text-purple-400",
    borderColor: "border-purple-500/10",
  },
  {
    step: 4,
    icon: FileTextIcon,
    title: "Structured report",
    body: "Receive a complete GTM report: Executive Summary, Market Sizing, Competitive Landscape, Segments, Risks, and Sources.",
    accent: "from-rose-500/20 to-rose-500/5",
    iconColor: "text-rose-400",
    borderColor: "border-rose-500/10",
  },
];

export function HowItWorksSection({ className }: { className?: string }) {
  return (
    <Section
      id="how-it-works"
      className={className}
      title="How It Works"
      subtitle="From question to structured intelligence in four steps"
    >
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {STEPS.map(({ step, icon: Icon, title, body, accent, iconColor, borderColor }) => (
          <div
            key={step}
            className={`group relative flex flex-col rounded-xl border ${borderColor} bg-gradient-to-b ${accent} p-6 transition-all duration-300 hover:border-white/10`}
          >
            <div className="mb-4 flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-lg bg-white/[0.04]">
                <Icon className={`size-5 ${iconColor}`} />
              </div>
              <span className="text-xs font-medium tracking-widest text-white/20 uppercase">
                Step {step}
              </span>
            </div>
            <h3 className="mb-2 text-lg font-semibold text-white/80">
              {title}
            </h3>
            <p className="text-sm leading-relaxed text-white/35">{body}</p>
          </div>
        ))}
      </div>

      {/* Connecting line */}
      <div className="mt-8 hidden items-center justify-center lg:flex">
        <div className="h-px w-full max-w-2xl bg-gradient-to-r from-transparent via-amber-500/15 to-transparent" />
      </div>
    </Section>
  );
}
