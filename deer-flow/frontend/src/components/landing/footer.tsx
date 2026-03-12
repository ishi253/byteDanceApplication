"use client";

import { useMemo } from "react";

export function Footer() {
  const year = useMemo(() => new Date().getFullYear(), []);
  return (
    <footer className="container-md mx-auto mt-16 flex flex-col items-center justify-center px-6 pb-12">
      <hr className="m-0 h-px w-full border-none bg-gradient-to-r from-transparent via-amber-500/15 to-transparent" />
      <div className="mt-8 flex flex-col items-center gap-3">
        <div className="flex items-center gap-2">
          <div className="flex size-5 items-center justify-center rounded bg-gradient-to-br from-amber-500 to-teal-400">
            <svg
              width="10"
              height="10"
              viewBox="0 0 16 16"
              fill="none"
              xmlns="http://www.w3.org/2000/svg"
            >
              <path
                d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z"
                fill="white"
                fillOpacity="0.9"
              />
            </svg>
          </div>
          <span className="font-serif text-sm text-white/40">Meridian</span>
        </div>
        <p className="text-center text-xs text-white/20">
          AI-powered GTM research agent
        </p>
        <p className="text-xs text-white/15">&copy; {year} Meridian</p>
      </div>
    </footer>
  );
}
