import { Footer } from "@/components/landing/footer";
import { Header } from "@/components/landing/header";
import { Hero } from "@/components/landing/hero";
import { CapabilitiesSection } from "@/components/landing/sections/capabilities-section";
import { HowItWorksSection } from "@/components/landing/sections/how-it-works-section";
import { ReportPreviewSection } from "@/components/landing/sections/report-preview-section";

export default function LandingPage() {
  return (
    <div className="noise-overlay min-h-screen w-full bg-[#0B1120]">
      <Header />
      <main className="flex w-full flex-col">
        <Hero />
        <HowItWorksSection />
        <CapabilitiesSection />
        <ReportPreviewSection />
      </main>
      <Footer />
    </div>
  );
}
