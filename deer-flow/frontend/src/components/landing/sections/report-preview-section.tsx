"use client";

import { ArrowRightIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

import { Section } from "../section";

export function ReportPreviewSection({ className }: { className?: string }) {
  return (
    <Section
      id="reports"
      className={className}
      title="Intelligence, Structured"
      subtitle="Every report follows a rigorous framework with traceable sources and confidence indicators"
    >
      <div className="mx-auto max-w-3xl">
        {/* Mock report outline */}
        <div className="meridian-card rounded-2xl p-8 md:p-10">
          <div className="mb-6 flex items-center gap-3">
            <div className="h-3 w-3 rounded-full bg-amber-500/50" />
            <span className="font-serif text-lg text-white/70">
              EV Charging Infrastructure — European Market
            </span>
          </div>

          <div className="space-y-4">
            {[
              {
                section: "Executive Summary",
                detail: "Market overview, key findings, strategic recommendation",
                confidence: "High",
                confidenceColor: "text-emerald-400",
              },
              {
                section: "Market Sizing (TAM/SAM/SOM)",
                detail: "Bottom-up estimates from 12 sources, 2024-2030 CAGR projections",
                confidence: "High",
                confidenceColor: "text-emerald-400",
              },
              {
                section: "Competitive Landscape",
                detail: "8 key players mapped, market share estimates, positioning matrix",
                confidence: "Medium",
                confidenceColor: "text-amber-400",
              },
              {
                section: "Customer Segments",
                detail: "3 primary segments with adoption drivers and friction points",
                confidence: "High",
                confidenceColor: "text-emerald-400",
              },
              {
                section: "Regulatory & Risk Analysis",
                detail: "EU directive analysis, country-specific requirements, timeline",
                confidence: "High",
                confidenceColor: "text-emerald-400",
              },
              {
                section: "Methodology & Sources",
                detail: "18 citations, source quality assessment, data recency audit",
                confidence: null,
                confidenceColor: null,
              },
            ].map(({ section, detail, confidence, confidenceColor }) => (
              <div
                key={section}
                className="flex items-start justify-between gap-4 border-b border-white/[0.04] pb-4 last:border-0 last:pb-0"
              >
                <div className="flex-1">
                  <h4 className="text-sm font-medium text-white/60">
                    {section}
                  </h4>
                  <p className="mt-1 text-xs text-white/25">{detail}</p>
                </div>
                {confidence && (
                  <span
                    className={`mt-0.5 shrink-0 text-xs font-medium ${confidenceColor}`}
                  >
                    {confidence}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Bottom CTA */}
        <div className="mt-12 flex flex-col items-center gap-4">
          <p className="text-sm text-white/25">
            Upload your own data to get even richer analysis
          </p>
          <Button
            size="lg"
            asChild
            className="group bg-gradient-to-r from-amber-500 to-amber-600 px-8 text-base font-medium text-white hover:from-amber-400 hover:to-amber-500 border-0"
          >
            <Link href="/workspace">
              Try It Now
              <ArrowRightIcon className="ml-2 size-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </Button>
        </div>
      </div>
    </Section>
  );
}
