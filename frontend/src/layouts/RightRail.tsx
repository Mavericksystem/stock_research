import { lazy, memo, Suspense, type ReactNode } from "react";
import { motion } from "framer-motion";
import { ChevronDown, PanelRight, PanelRightClose } from "lucide-react";

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
import { RAIL_SECTIONS, useRail, type RailSectionId } from "./rail/rail-context";

// Lazy-loaded: each panel (and its deps, e.g. recharts for GraphsPanel) is
// its own chunk, fetched only when the user actually opens that section.
const NewsPanel = lazy(() => import("../features/news/NewsPanel"));
const GraphsPanel = lazy(() => import("../features/graphs/GraphsPanel"));
const AnomaliesPanel = lazy(() => import("../features/anomalies/AnomaliesPanel"));

function RailPanelFallback() {
    return (
        <div className="px-2.5 py-6 text-center font-mono text-[11px] text-white/25">
            Loading…
        </div>
    );
}

interface RightRailProps {
    onEventSelect: (question: string) => void;
}



function RightRail({ onEventSelect }: RightRailProps) {
    const { state, isMobile, setOpen } = useSidebar();
    const { section, toggleSection, openSection, closeRail } = useRail();


    const expanded = !isMobile && state === "expanded";

    const renderPanel = (id: RailSectionId) => {
        let panel: ReactNode;

        switch (id) {
            case "news":
                panel = <NewsPanel />;
                break;
            case "graphs":
                panel = <GraphsPanel />;
                break;
            case "anomalies":
                panel = (
                    <AnomaliesPanel
                        onEventSelect={(question) => {
                            onEventSelect(question);
                            closeRail();
                        }}
                    />
                );
                break;
        }

        return <Suspense fallback={<RailPanelFallback />}>{panel}</Suspense>;
    };

    return (
        <TooltipProvider delay={0}>

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
                className="z-40 border-l border-white/[0.06] shadow-[-4px_0_12px_rgba(0,0,0,0.12)] transition-[width,right] duration-300 ease-[cubic-bezier(0.32,0.72,0,1)] group-data-[state=expanded]:w-(--rail-width)"
            >
                <SidebarHeader className="h-16 shrink-0 flex-row items-center justify-between gap-2 border-b border-white/[0.04] bg-white/[0.015] shadow-[0_1px_8px_rgba(0,0,0,0.18)] px-3 group-data-[collapsible=icon]:justify-center group-data-[collapsible=icon]:px-0">

                    <div className="hidden md:flex">
                        <SidebarMenu>
                            <SidebarMenuItem>
                                <SidebarMenuButton
                                    type="button"
                                    onClick={() => setOpen(!expanded)}
                                >
                                    {expanded ? (
                                        <PanelRightClose className="size-4" />
                                    ) : (
                                        <PanelRight className="size-4" />
                                    )}
                                </SidebarMenuButton>
                            </SidebarMenuItem>
                        </SidebarMenu>
                    </div>
                </SidebarHeader>

                {/* overflow-hidden: the open panel owns scrolling, not the rail. */}
                <SidebarContent className="gap-0 overflow-hidden">

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


                    <div className="flex min-h-0 flex-1 flex-col gap-2 p-2 group-data-[collapsible=icon]:hidden">
                        {RAIL_SECTIONS.map(({ id, label, icon: Icon }) => {
                            const open = section === id;

                            return (
                                <SidebarGroup
                                    key={id}
                                    data-open={open || undefined}
                                    className={cn(
                                        "min-h-0 gap-0 overflow-hidden rounded-xl border-l-2 p-0 transition-[background-color,border-color,box-shadow] duration-200",
                                        open
                                            ? "flex-1 border-l-[var(--amber)] bg-[var(--surface)] shadow-[inset_0_1px_0_0_rgba(255,255,255,0.04),0_4px_14px_rgba(0,0,0,0.28)] ring-1 ring-[var(--border-soft)]"
                                            : "flex-none rounded-lg border border-white/[0.05] bg-white/[0.015] shadow-[0_2px_8px_rgba(0,0,0,0.18)]",
                                    )}
                                >
                                    <button
                                        type="button"
                                        aria-expanded={open}
                                        aria-controls={`rail-panel-${id}`}
                                        onClick={() => toggleSection(id)}
                                        className={cn(
                                            "flex h-11 w-full shrink-0 items-center rounded-lg px-3 font-mono text-[11px] uppercase tracking-[0.14em] transition-all duration-200 hover:bg-white/[0.04] hover:shadow-[0_3px_10px_rgba(0,0,0,0.22)]",
                                            open
                                                ? "text-[var(--text)]"
                                                : "text-[var(--text-dim)] hover:text-[var(--text)]",
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


export default memo(RightRail);
