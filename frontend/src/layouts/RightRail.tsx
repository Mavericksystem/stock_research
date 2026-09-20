"use client";

import { useState } from "react";

import {
    Sidebar,
    SidebarContent,
    SidebarGroup,
    SidebarGroupContent,
    SidebarGroupLabel,
    SidebarProvider,
    SidebarTrigger,
} from "@/components/ui/sidebar";

import NewsPanel from "../features/news/NewsPanel";
import GraphsPanel from "../features/graphs/GraphsPanel";
import AnomaliesPanel from "../features/anomalies/AnomaliesPanel";

type Section = "news" | "graphs" | "anomalies";

interface RightRailProps {
    onEventSelect: (question: string) => void;
}

export default function RightRail({
    onEventSelect,
}: RightRailProps) {
    const [section, setSection] = useState<Section>("news");

    return (
        <SidebarProvider
            style={
                {
                    "--sidebar-width": "320px",
                    "--sidebar-width-mobile": "85vw",
                } as React.CSSProperties
            }
        >
            <Sidebar side="right" collapsible="offcanvas">
                <div className="flex items-center justify-between border-b px-3 py-2">
                    <span className="text-sm font-semibold">
                        Stock Research
                    </span>

                    <SidebarTrigger />
                </div>

                <SidebarContent>
                    <SidebarGroup>
                        <SidebarGroupLabel
                            onClick={() => setSection("news")}
                            className="cursor-pointer"
                        >
                            NEWS
                        </SidebarGroupLabel>

                        {section === "news" && (
                            <SidebarGroupContent>
                                <NewsPanel />
                            </SidebarGroupContent>
                        )}
                    </SidebarGroup>

                    <SidebarGroup>
                        <SidebarGroupLabel
                            onClick={() => setSection("graphs")}
                            className="cursor-pointer"
                        >
                            GRAPHS
                        </SidebarGroupLabel>

                        {section === "graphs" && (
                            <SidebarGroupContent>
                                <GraphsPanel />
                            </SidebarGroupContent>
                        )}
                    </SidebarGroup>

                    <SidebarGroup>
                        <SidebarGroupLabel
                            onClick={() => setSection("anomalies")}
                            className="cursor-pointer"
                        >
                            ANOMALIES
                        </SidebarGroupLabel>

                        {section === "anomalies" && (
                            <SidebarGroupContent>
                                <AnomaliesPanel
                                    onEventSelect={onEventSelect}
                                />
                            </SidebarGroupContent>
                        )}
                    </SidebarGroup>
                </SidebarContent>
            </Sidebar>
        </SidebarProvider>
    );
}