import { useSidebar } from "@/components/ui/sidebar";
import { cn } from "@/lib/utils";

import { RAIL_SECTIONS, useRail } from "./rail-context";

/**
 * Mobile-only icon strip.
 *
 * On desktop the collapsed sidebar *is* the icon strip (`collapsible="icon"`),
 * but on mobile the sidebar is a sheet — closed means nothing on screen. So the
 * strip is rendered as a real in-flow column next to the chat instead of a
 * fixed overlay: it sits under the header automatically and never covers
 * content, which a `position: fixed` strip would.
 */
export default function RailIconStrip({ className }: { className?: string }) {
    const { section, openSection } = useRail();
    const { openMobile } = useSidebar();

    return (
        <nav
            aria-label="Research panels"
            className={cn(
                "flex w-12 shrink-0 flex-col items-center gap-1 border-l border-[var(--border)] py-3",
                className,
            )}
        >
            {RAIL_SECTIONS.map(({ id, label, icon: Icon }) => {
                const active = openMobile && section === id;

                return (
                    <button
                        key={id}
                        type="button"
                        onClick={() => openSection(id)}
                        aria-label={label}
                        aria-pressed={active}
                        className={cn(
                            "flex size-9 items-center justify-center rounded-lg transition-colors duration-200 active:scale-95",
                            active
                                ? "bg-[var(--surface-2)] text-[var(--amber)]"
                                : "text-[var(--text-dim)] hover:bg-[var(--surface)] hover:text-[var(--text)]",
                        )}
                    >
                        <Icon className="size-[18px]" />
                    </button>
                );
            })}
        </nav>
    );
}
