"use client";

import { ArrowRightIcon } from "lucide-react";
import Link from "next/link";

import { Button } from "@/components/ui/button";

export function Header() {
  return (
    <header className="container-md fixed top-0 right-0 left-0 z-20 mx-auto flex h-16 items-center justify-between px-6 backdrop-blur-md">
      <div className="flex items-center gap-3">
        <div className="flex size-8 items-center justify-center rounded-lg bg-gradient-to-br from-amber-500 to-teal-400">
          <svg
            width="16"
            height="16"
            viewBox="0 0 16 16"
            fill="none"
            xmlns="http://www.w3.org/2000/svg"
          >
            <path
              d="M8 1L14 4.5V11.5L8 15L2 11.5V4.5L8 1Z"
              fill="white"
              fillOpacity="0.9"
            />
            <path d="M8 5L11 7V11L8 13L5 11V7L8 5Z" fill="#0B1120" />
          </svg>
        </div>
        <span className="font-serif text-xl tracking-tight text-white/90">
          Meridian
        </span>
      </div>
      <div className="flex items-center gap-4">
        <nav className="hidden items-center gap-6 md:flex">
          <a
            href="#how-it-works"
            className="text-sm text-white/50 transition-colors hover:text-white/80"
          >
            How It Works
          </a>
          <a
            href="#capabilities"
            className="text-sm text-white/50 transition-colors hover:text-white/80"
          >
            Capabilities
          </a>
          <a
            href="#reports"
            className="text-sm text-white/50 transition-colors hover:text-white/80"
          >
            Reports
          </a>
        </nav>
        <Button
          size="sm"
          asChild
          className="bg-gradient-to-r from-amber-500 to-amber-600 text-white hover:from-amber-400 hover:to-amber-500 border-0"
        >
          <Link href="/workspace">
            Launch Agent
            <ArrowRightIcon className="ml-1 size-3.5" />
          </Link>
        </Button>
      </div>
      <hr className="absolute top-16 right-0 left-0 z-10 m-0 h-px w-full border-none bg-gradient-to-r from-transparent via-amber-500/20 to-transparent" />
    </header>
  );
}
