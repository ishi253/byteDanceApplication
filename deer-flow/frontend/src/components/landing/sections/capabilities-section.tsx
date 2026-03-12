"use client";

import {
  BarChart3Icon,
  GlobeIcon,
  LayersIcon,
  ShieldIcon,
  TrendingUpIcon,
  UsersIcon,
} from "lucide-react";

import { Section } from "../section";

const CAPABILITIES = [
  {
    icon: BarChart3Icon,
    title: "TAM / SAM / SOM",
    description:
      "Bottom-up and top-down market sizing with source-backed estimates and growth projections.",
    color: "text-amber-400",
    bg: "bg-amber-500/5",
    border: "border-amber-500/10",
  },
  {
    icon: GlobeIcon,
    title: "Competitive Landscape",
    description:
      "Map key players, market share estimates, positioning matrices, and strategic moats.",
    color: "text-teal-400",
    bg: "bg-teal-500/5",
    border: "border-teal-500/10",
  },
  {
    icon: UsersIcon,
    title: "Customer Segments",
    description:
      "Identify target segments with persona profiles, pain points, and willingness-to-pay signals.",
    color: "text-purple-400",
    bg: "bg-purple-500/5",
    border: "border-purple-500/10",
  },
  {
    icon: TrendingUpIcon,
    title: "Trends & Drivers",
    description:
      "Surface macro and micro trends shaping the market, with recency and velocity indicators.",
    color: "text-rose-400",
    bg: "bg-rose-500/5",
    border: "border-rose-500/10",
  },
  {
    icon: ShieldIcon,
    title: "Regulatory & Risk",
    description:
      "Flag regulatory hurdles, compliance requirements, and market-specific risk factors.",
    color: "text-sky-400",
    bg: "bg-sky-500/5",
    border: "border-sky-500/10",
  },
  {
    icon: LayersIcon,
    title: "PDF & Data Ingestion",
    description:
      "Upload proprietary reports and datasets. RAG-powered retrieval enriches every analysis.",
    color: "text-emerald-400",
    bg: "bg-emerald-500/5",
    border: "border-emerald-500/10",
  },
];

export function CapabilitiesSection({ className }: { className?: string }) {
  return (
    <Section
      id="capabilities"
      className={className}
      title="Research Capabilities"
      subtitle="Every report section is backed by live data, cross-validated sources, and confidence scoring"
    >
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
        {CAPABILITIES.map(({ icon: Icon, title, description, color, bg, border }) => (
          <div
            key={title}
            className={`group relative flex flex-col rounded-xl border ${border} ${bg} p-6 transition-all duration-300 hover:border-white/10`}
          >
            <div className={`mb-4 flex size-10 items-center justify-center rounded-lg bg-white/[0.04]`}>
              <Icon className={`size-5 ${color}`} />
            </div>
            <h3 className="mb-2 text-base font-semibold text-white/80">
              {title}
            </h3>
            <p className="text-sm leading-relaxed text-white/35">
              {description}
            </p>
          </div>
        ))}
      </div>
    </Section>
  );
}
