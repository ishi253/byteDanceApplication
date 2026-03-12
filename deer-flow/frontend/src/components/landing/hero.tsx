"use client";

import { ArrowRightIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";
import { WordRotate } from "@/components/ui/word-rotate";
import { cn } from "@/lib/utils";

const EXAMPLE_TOPICS = [
  "EV Charging Market in Europe",
  "Cloud Kitchen Industry in SEA",
  "AI Tutoring Startups in India",
  "Vertical SaaS for Healthcare",
];

export function Hero({ className }: { className?: string }) {
  return (
    <div
      className={cn(
        "relative flex min-h-screen w-full flex-col items-center justify-center overflow-hidden",
        className,
      )}
    >
      {/* Ambient background effects */}
      <div className="pointer-events-none absolute inset-0">
        {/* Top-right amber glow */}
        <div
          className="absolute -top-32 right-0 h-[600px] w-[600px] rounded-full opacity-[0.07]"
          style={{
            background:
              "radial-gradient(circle, #E8A838 0%, transparent 70%)",
          }}
        />
        {/* Bottom-left teal glow */}
        <div
          className="absolute -bottom-48 -left-32 h-[500px] w-[500px] rounded-full opacity-[0.05]"
          style={{
            background:
              "radial-gradient(circle, #2DD4BF 0%, transparent 70%)",
          }}
        />
        {/* Diagonal grid lines */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `
              linear-gradient(30deg, rgba(255,255,255,0.1) 1px, transparent 1px),
              linear-gradient(-30deg, rgba(255,255,255,0.1) 1px, transparent 1px)
            `,
            backgroundSize: "60px 100px",
          }}
        />
        {/* Horizontal scan lines */}
        <div
          className="absolute inset-0 opacity-[0.02]"
          style={{
            backgroundImage:
              "repeating-linear-gradient(0deg, transparent, transparent 2px, rgba(255,255,255,0.1) 2px, rgba(255,255,255,0.1) 3px)",
          }}
        />
      </div>

      <div className="container-md relative z-10 mx-auto flex flex-col items-center px-6 pt-24">
        {/* Eyebrow badge */}
        <div className="mb-8 inline-flex items-center gap-2 rounded-full border border-amber-500/20 bg-amber-500/5 px-4 py-1.5">
          <div className="h-1.5 w-1.5 rounded-full bg-amber-400 animate-pulse" />
          <span className="text-xs font-medium tracking-widest text-amber-400/90 uppercase">
            AI-Powered Market Intelligence
          </span>
        </div>

        {/* Main heading */}
        <h1 className="text-center font-serif text-5xl leading-[1.1] tracking-tight md:text-7xl lg:text-8xl">
          <span className="block text-white/90">
            <WordRotate
              words={[
                "Market Sizing",
                "Competitive Intel",
                "Go-to-Market",
                "Industry Analysis",
                "Entry Strategy",
                "Customer Segments",
              ]}
            />
          </span>
          <span className="amber-glow mt-2 block">in minutes, not weeks.</span>
        </h1>

        {/* Subtitle */}
        <p className="mt-8 max-w-2xl text-center text-lg leading-relaxed text-white/40 md:text-xl">
          Structured GTM reports with TAM/SAM/SOM analysis, competitive
          landscapes, confidence-scored insights, and full source citations.
        </p>

        {/* CTA */}
        <div className="mt-10 flex flex-col items-center gap-4 sm:flex-row">
          <Button
            size="lg"
            asChild
            className="group bg-gradient-to-r from-amber-500 to-amber-600 px-8 text-base font-medium text-white hover:from-amber-400 hover:to-amber-500 border-0"
          >
            <Link href="/workspace">
              Start Research
              <ArrowRightIcon className="ml-2 size-4 transition-transform group-hover:translate-x-0.5" />
            </Link>
          </Button>
        </div>

        {/* Example topics */}
        <div className="mt-16 flex flex-col items-center gap-3">
          <span className="text-xs font-medium tracking-widest text-white/25 uppercase">
            Try a topic
          </span>
          <div className="flex flex-wrap justify-center gap-2">
            {EXAMPLE_TOPICS.map((topic) => (
              <Link
                key={topic}
                href={`/workspace/chats/new?q=${encodeURIComponent(topic)}`}
              >
                <span className="inline-flex cursor-pointer rounded-full border border-white/[0.06] bg-white/[0.02] px-4 py-2 text-sm text-white/40 transition-all hover:border-amber-500/20 hover:bg-amber-500/5 hover:text-amber-400/70">
                  {topic}
                </span>
              </Link>
            ))}
          </div>
        </div>

        {/* Data visualization decorative element */}
        <div className="mt-20 mb-8 w-full max-w-3xl">
          <div className="meridian-card rounded-2xl p-8">
            <div className="mb-4 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div className="h-2 w-2 rounded-full bg-amber-500/60" />
                <span className="text-xs font-medium tracking-wider text-white/30 uppercase">
                  Sample Output
                </span>
              </div>
              <span className="text-xs text-white/20">
                Confidence: High (4 sources)
              </span>
            </div>
            <div className="space-y-3">
              <div className="flex items-center gap-3">
                <span className="w-20 text-right text-xs text-white/25">
                  TAM
                </span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/[0.04]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-amber-500/60 to-amber-400/40"
                    style={{ width: "85%" }}
                  />
                </div>
                <span className="w-16 text-xs font-medium text-amber-400/60">
                  $42.3B
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-20 text-right text-xs text-white/25">
                  SAM
                </span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/[0.04]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-teal-500/60 to-teal-400/40"
                    style={{ width: "52%" }}
                  />
                </div>
                <span className="w-16 text-xs font-medium text-teal-400/60">
                  $18.7B
                </span>
              </div>
              <div className="flex items-center gap-3">
                <span className="w-20 text-right text-xs text-white/25">
                  SOM
                </span>
                <div className="h-2 flex-1 overflow-hidden rounded-full bg-white/[0.04]">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-purple-500/60 to-purple-400/40"
                    style={{ width: "18%" }}
                  />
                </div>
                <span className="w-16 text-xs font-medium text-purple-400/60">
                  $3.2B
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
