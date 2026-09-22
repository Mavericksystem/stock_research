import {
    createContext,
    useCallback,
    useContext,
    useMemo,
    useState,
    type ComponentType,
    type ReactNode,
} from "react";
import { Newspaper, TrendingUp, Zap } from "lucide-react";

import { useSidebar } from "@/components/ui/sidebar";

export type RailSectionId = "news" | "graphs" | "anomalies";

export interface RailSection {
    id: RailSectionId;
    label: string;
    icon: ComponentType<{ className?: string }>;
}

/**
 * Single source of truth for the rail — the mobile icon strip, the collapsed
 * desktop icon menu and the expanded accordion all render from this list.
 */
export const RAIL_SECTIONS: readonly RailSection[] = [
    { id: "news", label: "News", icon: Newspaper },
    { id: "graphs", label: "Graphs", icon: TrendingUp },
    { id: "anomalies", label: "Anomalies", icon: Zap },
];

interface RailContextValue {
    /** Currently expanded accordion section. `null` = all collapsed. */
    section: RailSectionId | null;
    /** Accordion behaviour: clicking the open section closes it. */
    toggleSection: (id: RailSectionId) => void;
    /** Icon-strip behaviour: select a section and open the rail. */
    openSection: (id: RailSectionId) => void;
    /** Close the rail — used when an action hands the screen back to the chat. */
    closeRail: () => void;
}

const RailContext = createContext<RailContextValue | null>(null);

export function useRail(): RailContextValue {
    const context = useContext(RailContext);
    if (!context) {
        throw new Error("useRail must be used within a RailProvider.");
    }
    return context;
}

/**
 * Must be mounted inside SidebarProvider — it reads the sidebar's open state so
 * a single call site can expand the rail on desktop and open the sheet on
 * mobile.
 */
export function RailProvider({ children }: { children: ReactNode }) {
    // Starts closed so no panel (and no panel fetch) mounts on initial load.
    // Panels are lazy-loaded, so the first open also triggers their chunk fetch.
    const [section, setSection] = useState<RailSectionId | null>(null);
    const { isMobile, setOpen, setOpenMobile } = useSidebar();

    const toggleSection = useCallback((id: RailSectionId) => {
        setSection((current) => (current === id ? null : id));
    }, []);

    const openSection = useCallback(
        (id: RailSectionId) => {
            setSection(id);
            if (isMobile) {
                setOpenMobile(true);
            } else {
                setOpen(true);
            }
        },
        [isMobile, setOpen, setOpenMobile],
    );

    const closeRail = useCallback(() => {
        if (isMobile) {
            setOpenMobile(false);
        } else {
            setOpen(false);
        }
    }, [isMobile, setOpen, setOpenMobile]);

    const value = useMemo<RailContextValue>(
        () => ({ section, toggleSection, openSection, closeRail }),
        [section, toggleSection, openSection, closeRail],
    );

    return <RailContext.Provider value={value}>{children}</RailContext.Provider>;
}
