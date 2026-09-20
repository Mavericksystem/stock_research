import { motion } from "framer-motion";
import { ChevronDown } from "lucide-react";

import {
    Sidebar,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupContent,
    SidebarHeader,
    SidebarMenu,
    SidebarMenuButton,
    SidebarMenuItem,
    useSidebar,
} from "@/components/ui/sidebar";
import { TooltipProvider } from "@/components/ui/tooltip";
import { cn } from "@/lib/utils";

import NewsPanel from "../features/news/NewsPanel";
import GraphsPanel from "../features/graphs/GraphsPanel";
import AnomaliesPanel from "../features/anomalies/AnomaliesPanel";
import { RAIL_SECTIONS, useRail, type RailSectionId } from "./rail/rail-context";

interface RightRailProps {
    onEventSelect: (question: string) => void;
}

/**
 * Right research rail.
 *
 * Layout model — deliberately an *overlay*, not a push:
 *   collapsed  → 3.5rem icon strip, always visible on desktop
 *   expanded   → 22rem panel that floats over the chat behind a blurred scrim
 *
 * shadcn's `collapsible="icon"` normally reflows the page when it expands. Here
 * `--sidebar-width` and `--sidebar-width-icon` are both set to the icon width
 * (see AppLayout), so the in-flow gap is a constant 3.5rem and only the fixed
 * container grows via `group-data-[state=expanded]:w-(--rail-width)`. The chat
 * never reflows, and the open/close reads identically on desktop and mobile:
 * panel slides in, background blurs.
 *
 * Inside, the three sections are an accordion (one open at a time). The open
 * section takes the remaining height so its own scroll container works; the
 * others collapse to their header row.
 */
export default function RightRail({ onEventSelect }: RightRailProps) {
    const { state, isMobile, setOpen } = useSidebar();
    const { section, toggleSection, openSection, closeRail } = useRail();

    // `state` is derived from desktop-only `open`, which defaults to true and
    // is independent of `openMobile` — so on mobile this was `true` from
    // first paint, before the sheet ever opened. Gate on `isMobile` too so
    // the value is never stale, on top of not rendering the scrim at all
    // below.
    const expanded = !isMobile && state === "expanded";

    const renderPanel = (id: RailSectionId) => {
        switch (id) {
            case "news":
                return <NewsPanel />;
            case "graphs":
                return <GraphsPanel />;
            case "anomalies":
                return (
                    <AnomaliesPanel
                        onEventSelect={(question) => {
                            onEventSelect(question);
                            closeRail();
                        }}
                    />
                );
        }
    };

    return (
        <TooltipProvider delay={0}>
            {/* Desktop-only scrim. Mobile gets an equivalent blurred backdrop
                for free from the Sheet's own SheetOverlay, so this must not
                even mount on mobile — not just be CSS-hidden. Relying on
                `hidden md:block` alone let it render (and blur the panel's
                own content) under stacking-context/portal edge cases on real
                devices; a JS-level `isMobile` guard makes that impossible. */}
            {!isMobile && (
                <div
                    aria-hidden="true"
                    onClick={() => setOpen(false)}
                    className={cn(
                        "fixed inset-0 z-30 bg-black/45 backdrop-blur-md transition-opacity duration-300 ease-out",
                        expanded ? "opacity-100" : "pointer-events-none opacity-0",
                    )}
                />
            )}

            <Sidebar
                side="right"
                collapsible="icon"
                className="z-40 border-[var(--border)] transition-[width,right] duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] group-data-[state=expanded]:w-(--rail-width)"
            >
                <SidebarHeader className="h-14 shrink-0 flex-row items-center justify-between gap-2 border-b border-[var(--border)] px-3 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0">
                    <span className="truncate font-mono text-[10px] uppercase tracking-[0.18em] text-[var(--text-dim)] group-data-[collapsible=icon]:hidden">
                        Research
                    </span>
                </SidebarHeader>

                {/* overflow-hidden: the open panel owns scrolling, not the rail. */}
                <SidebarContent className="gap-0 overflow-hidden">
                    {/* Collapsed state — icon menu. `group-data-*` only resolves on the
                        desktop wrapper, so this never renders inside the mobile sheet. */}
                    <SidebarGroup className="hidden p-1.5 group-data-[collapsible=icon]:block">
                        <SidebarMenu className="gap-1">
                            {RAIL_SECTIONS.map(({ id, label, icon: Icon }) => (
                                <SidebarMenuItem key={id}>
                                    <SidebarMenuButton
                                        type="button"
                                        tooltip={label}
                                        isActive={section === id}
                                        onClick={() => openSection(id)}
                                        className="justify-center text-[var(--text-dim)] hover:text-[var(--text)] data-active:text-[var(--amber)]"
                                    >
                                        <Icon className="size-[18px]" />
                                        <span className="sr-only">{label}</span>
                                    </SidebarMenuButton>
                                </SidebarMenuItem>
                            ))}
                        </SidebarMenu>
                    </SidebarGroup>

                    {/* Expanded state — accordion. */}
                    <div className="flex min-h-0 flex-1 flex-col group-data-[collapsible=icon]:hidden">
                        {RAIL_SECTIONS.map(({ id, label, icon: Icon }) => {
                            const open = section === id;

                            return (
                                <SidebarGroup
                                    key={id}
                                    data-open={open || undefined}
                                    className={cn(
                                        "min-h-0 gap-0 border-b border-[var(--border)] p-0",
                                        open ? "flex-1" : "flex-none",
                                    )}
                                >
                                    <button
                                        type="button"
                                        aria-expanded={open}
                                        aria-controls={`rail-panel-${id}`}
                                        onClick={() => toggleSection(id)}
                                        className={cn(
                                            "flex h-11 w-full shrink-0 items-center rounded-none px-3 font-mono text-[11px] uppercase tracking-[0.14em] transition-colors duration-200 hover:bg-white/[0.03]",
                                            open
                                                ? "text-[var(--text)]"
                                                : "text-[var(--text-muted)] hover:text-[var(--text)]",
                                        )}
                                    >
                                        <Icon
                                            className={cn(
                                                "size-4 transition-colors duration-200",
                                                open && "text-[var(--amber)]",
                                            )}
                                        />
                                        <span className="ml-2">{label}</span>
                                        <ChevronDown
                                            className={cn(
                                                "ml-auto size-4 transition-transform duration-300 ease-out",
                                                open && "rotate-180",
                                            )}
                                        />
                                    </button>

                                    {open && (
                                        <motion.div
                                            key={id}
                                            id={`rail-panel-${id}`}
                                            initial={{ opacity: 0, y: -6 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            transition={{ duration: 0.22, ease: "easeOut" }}
                                            className="min-h-0 flex-1 overflow-hidden"
                                        >
                                            <SidebarGroupContent className="h-full">
                                                {renderPanel(id)}
                                            </SidebarGroupContent>
                                        </motion.div>
                                    )}
                                </SidebarGroup>
                            );
                        })}
                    </div>
                </SidebarContent>

                <SidebarFooter className="shrink-0 px-3 py-2 group-data-[collapsible=icon]:hidden">
                    <span className="font-mono text-[10px] text-[var(--text-dim)]">
                        ⌘B / Ctrl+B to toggle
                    </span>
                </SidebarFooter>
            </Sidebar>
        </TooltipProvider>
    );
}
