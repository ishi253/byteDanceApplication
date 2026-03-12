import { cn } from "@/lib/utils";

export function Section({
  id,
  className,
  title,
  subtitle,
  children,
}: {
  id?: string;
  className?: string;
  title: React.ReactNode;
  subtitle?: React.ReactNode;
  children: React.ReactNode;
}) {
  return (
    <section
      id={id}
      className={cn("mx-auto flex w-full flex-col py-24 px-6", className)}
    >
      <header className="container-md mx-auto flex flex-col items-center justify-between">
        <div className="mb-2 font-serif text-center text-4xl tracking-tight text-white/90 md:text-5xl">
          {title}
        </div>
        {subtitle && (
          <div className="mt-3 max-w-2xl text-center text-lg text-white/35">
            {subtitle}
          </div>
        )}
      </header>
      <main className="container-md mx-auto mt-12 w-full">{children}</main>
    </section>
  );
}
