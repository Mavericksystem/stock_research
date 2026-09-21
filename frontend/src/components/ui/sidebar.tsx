"use client"

import * as React from "react"
import { cn } from "cn"
import { PanelLeftIcon } from "lucide-react"

import { useIsMobile } from "@/hooks/use-mobile"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from "@/components/ui/sheet"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"

const SIDEBAR_COOKIE_NAME = "sidebar_state"
const SIDEBAR_COOKIE_MAX_AGE = 60 * 60 * 24 * 7

const SIDEBAR_WIDTH = "16rem"
const SIDEBAR_WIDTH_MOBILE = "18rem"
const SIDEBAR_WIDTH_ICON = "3rem"
const SIDEBAR_KEYBOARD_SHORTCUT = "b"

type SidebarContextProps = {
  state: "expanded" | "collapsed"
  open: boolean
  setOpen: (
    open: boolean | ((open: boolean) => boolean)
  ) => void
  openMobile: boolean
  setOpenMobile: (open: boolean) => void
  isMobile: boolean
  toggleSidebar: () => void
}

const SidebarContext =
  React.createContext<SidebarContextProps | null>(null)

export function useSidebar() {
  const context = React.useContext(SidebarContext)

  if (!context) {
    throw new Error(
      "useSidebar must be used within a SidebarProvider."
    )
  }

  return context
}

/* -------------------------------------------------------------------------- */
/* Provider                                                                   */
/* -------------------------------------------------------------------------- */

export function SidebarProvider({
  defaultOpen = false,
  open: openProp,
  onOpenChange: setOpenProp,
  className,
  style,
  children,
  ...props
}: React.ComponentProps<"div"> & {
  defaultOpen?: boolean
  open?: boolean
  onOpenChange?: (open: boolean) => void
}) {
  const isMobile = useIsMobile()

  const [openMobile, setOpenMobile] = React.useState(false)
  const [_open, _setOpen] = React.useState(defaultOpen)

  const open = openProp ?? _open

  const setOpen = React.useCallback(
    (
      value:
        | boolean
        | ((value: boolean) => boolean)
    ) => {
      const next =
        typeof value === "function"
          ? value(open)
          : value

      if (setOpenProp) {
        setOpenProp(next)
      } else {
        _setOpen(next)
      }

      document.cookie =
        `${SIDEBAR_COOKIE_NAME}=${next}; path=/; max-age=${SIDEBAR_COOKIE_MAX_AGE}`
    },
    [open, setOpenProp]
  )

  const toggleSidebar = React.useCallback(() => {
    if (isMobile) {
      setOpenMobile((value) => !value)
    } else {
      setOpen((value) => !value)
    }
  }, [isMobile, setOpen])

  React.useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (
        event.key === SIDEBAR_KEYBOARD_SHORTCUT &&
        (event.metaKey || event.ctrlKey)
      ) {
        event.preventDefault()
        toggleSidebar()
      }
    }

    window.addEventListener(
      "keydown",
      handleKeyDown
    )

    return () =>
      window.removeEventListener(
        "keydown",
        handleKeyDown
      )
  }, [toggleSidebar])

  const state =
    open ? "expanded" : "collapsed"

  const contextValue =
    React.useMemo<SidebarContextProps>(
      () => ({
        state,
        open,
        setOpen,
        openMobile,
        setOpenMobile,
        isMobile,
        toggleSidebar,
      }),
      [
        state,
        open,
        setOpen,
        openMobile,
        isMobile,
        toggleSidebar,
      ]
    )

  return (
    <SidebarContext.Provider
      value={contextValue}
    >
      <div
        data-slot="sidebar-wrapper"
        data-state={state}
        className={cn(
          "group/sidebar-wrapper flex min-h-svh w-full",
          className
        )}
        style={
          {
            "--sidebar-width": SIDEBAR_WIDTH,
            "--sidebar-width-icon":
              SIDEBAR_WIDTH_ICON,
            ...style,
          } as React.CSSProperties
        }
        {...props}
      >
        {children}
      </div>
    </SidebarContext.Provider>
  )
}

/* -------------------------------------------------------------------------- */
/* Sidebar                                                                    */
/* -------------------------------------------------------------------------- */

export function Sidebar({
  side = "left",
  variant = "sidebar",
  collapsible = "offcanvas",
  className,
  children,
  dir,
  ...props
}: React.ComponentProps<"div"> & {
  side?: "left" | "right"
  variant?: "sidebar" | "floating" | "inset"
  collapsible?: "offcanvas" | "icon" | "none"
}) {
  const {
    isMobile,
    state,
    openMobile,
    setOpenMobile,
  } = useSidebar()

  /* ------------------------------ no collapse ---------------------------- */

  if (collapsible === "none") {
    return (
      <div
        data-slot="sidebar"
        data-side={side}
        data-variant={variant}
        className={cn(
          "flex h-full w-(--sidebar-width) flex-col",
          "bg-sidebar text-sidebar-foreground",
          className
        )}
        {...props}
      >
        {children}
      </div>
    )
  }

  /* ------------------------------- mobile -------------------------------- */

  if (isMobile) {
    return (
      <Sheet
        open={openMobile}
        onOpenChange={setOpenMobile}
      >
        <SheetContent
          dir={dir}
          side={side}
          data-sidebar="sidebar"
          data-slot="sidebar"
          data-mobile="true"
          className={cn(
            "w-(--sidebar-width)",
            "bg-transparent p-0",
            "text-sidebar-foreground",
            "shadow-none",
            "[&>button]:hidden"
          )}
          style={
            {
              "--sidebar-width":
                `var(--sidebar-width-mobile, ${SIDEBAR_WIDTH_MOBILE})`,
            } as React.CSSProperties
          }
        >
          <SheetHeader className="sr-only">
            <SheetTitle>
              Sidebar
            </SheetTitle>

            <SheetDescription>
              Displays the mobile sidebar.
            </SheetDescription>
          </SheetHeader>

          {/* Mobile surface intentionally unchanged:
              no backdrop blur on the animated Sheet node. */}
          <div
            data-slot="sidebar-mobile-surface"
            className={cn(
              "flex h-full w-full flex-col",
              "border-[var(--border)]",
              "bg-[var(--sidebar)]",
              "shadow-lg",
              side === "right"
                ? "border-l"
                : "border-r"
            )}
          >
            {children}
          </div>
        </SheetContent>
      </Sheet>
    )
  }

  /* ------------------------------- desktop ------------------------------- */

  return (
    <div
      data-slot="sidebar"
      data-side={side}
      data-state={state}
      data-variant={variant}
      data-collapsible={
        state === "collapsed"
          ? collapsible
          : ""
      }
      className={cn(
        "group peer hidden text-sidebar-foreground md:block",
        className
      )}
      {...props}
    >
      {/* Permanent 3.5rem layout gap.
          AppLayout intentionally sets sidebar-width to 3.5rem. */}
      <div
        data-slot="sidebar-gap"
        className={cn(
          "relative shrink-0",
          "w-(--sidebar-width)",
          "transition-[width] duration-300",
          "ease-[cubic-bezier(0.32,0.72,0,1)]"
        )}
      />

      {/* Fixed visual rail */}
      <div
        data-slot="sidebar-container"
        data-side={side}
        className={cn(
          "fixed inset-y-0 z-40",
          "hidden h-svh md:flex",
          "w-(--sidebar-width-icon)",
          "transition-[width,right,left]",
          "duration-300",
          "ease-[cubic-bezier(0.32,0.72,0,1)]",

          side === "right"
            ? "right-0"
            : "left-0",

          side === "right"
            ? "group-data-[collapsible=offcanvas]:right-[calc(var(--sidebar-width)*-1)]"
            : "group-data-[collapsible=offcanvas]:left-[calc(var(--sidebar-width)*-1)]",

          "group-data-[state=expanded]:w-(--rail-width)"
        )}
      >
        <div
          data-sidebar="sidebar"
          data-slot="sidebar-inner"
          className={cn(
            "flex size-full flex-col",
            "bg-[var(--sidebar-glass)]",
            "backdrop-blur-xl",
            "text-sidebar-foreground",

            side === "right"
              ? "border-l border-white/[0.06] shadow-[-4px_0_12px_rgba(0,0,0,0.12)]"
              : "border-r border-white/[0.06]"
          )}
        >
          {children}
        </div>
      </div>
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/* Trigger                                                                    */
/* -------------------------------------------------------------------------- */

export function SidebarTrigger({
  className,
  onClick,
  children,
  ...props
}: React.ComponentProps<"button">) {
  const { toggleSidebar } = useSidebar()

  return (
    <button
      type="button"
      data-sidebar="trigger"
      data-slot="sidebar-trigger"
      aria-label="Toggle sidebar"
      className={cn(
        "inline-flex size-8 shrink-0",
        "items-center justify-center",
        "rounded-md",
        "text-muted-foreground",
        "transition-all duration-200",
        "hover:bg-muted",
        "hover:text-foreground",
        "active:scale-95",
        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-ring",
        className
      )}
      onClick={(event) => {
        onClick?.(event)
        toggleSidebar()
      }}
      {...props}
    >
      {children ?? (
        <PanelLeftIcon className="size-4" />
      )}

      <span className="sr-only">
        Toggle Sidebar
      </span>
    </button>
  )
}

/* -------------------------------------------------------------------------- */
/* Layout                                                                      */
/* -------------------------------------------------------------------------- */

export function SidebarInset({
  className,
  ...props
}: React.ComponentProps<"main">) {
  return (
    <main
      data-slot="sidebar-inset"
      className={cn(
        "relative flex min-w-0 flex-1 flex-col",
        "bg-background",
        className
      )}
      {...props}
    />
  )
}

export function SidebarHeader({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sidebar-header"
      className={cn(
        "flex shrink-0 items-center gap-2 p-3",
        "group-data-[collapsible=icon]:justify-center",
        "group-data-[collapsible=icon]:px-0",
        className
      )}
      {...props}
    />
  )
}

export function SidebarContent({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sidebar-content"
      className={cn(
        "flex min-h-0 flex-1 flex-col",
        "overflow-auto",
        "group-data-[collapsible=icon]:overflow-hidden",
        className
      )}
      {...props}
    />
  )
}

export function SidebarFooter({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sidebar-footer"
      className={cn(
        "flex shrink-0 flex-col gap-2 p-3",
        className
      )}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/* Groups                                                                     */
/* -------------------------------------------------------------------------- */

export function SidebarGroup({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sidebar-group"
      className={cn(
        "relative flex min-w-0 flex-col p-2",
        className
      )}
      {...props}
    />
  )
}

export function SidebarGroupLabel({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sidebar-group-label"
      className={cn(
        "flex h-8 shrink-0 items-center",
        "rounded-md px-2",
        "text-xs font-medium",
        "text-sidebar-foreground/70",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}

export function SidebarGroupAction({
  className,
  ...props
}: React.ComponentProps<"button">) {
  return (
    <button
      type="button"
      data-slot="sidebar-group-action"
      className={cn(
        "absolute right-3 top-3",
        "flex size-5 items-center justify-center",
        "rounded-md",
        "text-sidebar-foreground/70",
        "hover:bg-sidebar-accent",
        "hover:text-sidebar-accent-foreground",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}

export function SidebarGroupContent({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sidebar-group-content"
      className={cn(
        "w-full min-w-0",
        className
      )}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/* Menu                                                                       */
/* -------------------------------------------------------------------------- */

export function SidebarMenu({
  className,
  ...props
}: React.ComponentProps<"ul">) {
  return (
    <ul
      data-slot="sidebar-menu"
      className={cn(
        "flex w-full min-w-0 flex-col gap-1",
        className
      )}
      {...props}
    />
  )
}

export function SidebarMenuItem({
  className,
  ...props
}: React.ComponentProps<"li">) {
  return (
    <li
      data-slot="sidebar-menu-item"
      className={cn(
        "group/menu-item relative",
        className
      )}
      {...props}
    />
  )
}

export function SidebarMenuButton({
  className,
  tooltip,
  isActive = false,
  size = "default",
  ...props
}: React.ComponentProps<"button"> & {
  tooltip?: string
  isActive?: boolean
  size?: "default" | "sm" | "lg"
}) {
  const { state } = useSidebar()

  const sizeClass =
    size === "sm"
      ? "h-7 text-xs"
      : size === "lg"
        ? "h-12 text-sm"
        : "h-8 text-sm"

  const button = (
    <button
      type="button"
      data-slot="sidebar-menu-button"
      data-sidebar="menu-button"
      data-active={
        isActive ? "true" : undefined
      }
      data-size={size}
      className={cn(
        "flex w-full min-w-0 items-center",
        "gap-2 overflow-hidden",
        "rounded-md px-2",
        "text-left",
        "text-sidebar-foreground",
        sizeClass,

        "transition-all duration-200",

        "hover:bg-sidebar-accent",
        "hover:text-sidebar-accent-foreground",

        "focus-visible:outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-sidebar-ring",

        "active:scale-[0.98]",

        "data-[active=true]:bg-sidebar-accent",
        "data-[active=true]:text-sidebar-accent-foreground",

        "group-data-[collapsible=icon]:justify-center",
        "group-data-[collapsible=icon]:px-0",

        "[&_svg]:size-4",
        "[&_svg]:shrink-0",

        className
      )}
      {...props}
    />
  )

  if (
    state === "expanded" ||
    !tooltip
  ) {
    return button
  }

  return (
    <Tooltip>
      <TooltipTrigger
        render={button}
      />

      <TooltipContent side="left">
        {tooltip}
      </TooltipContent>
    </Tooltip>
  )
}

export function SidebarMenuAction({
  className,
  ...props
}: React.ComponentProps<"button">) {
  return (
    <button
      type="button"
      data-slot="sidebar-menu-action"
      className={cn(
        "absolute right-1 top-1.5",
        "flex size-5 items-center justify-center",
        "rounded-md",
        "text-sidebar-foreground/70",
        "hover:bg-sidebar-accent",
        "hover:text-sidebar-accent-foreground",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}

export function SidebarMenuBadge({
  className,
  ...props
}: React.ComponentProps<"span">) {
  return (
    <span
      data-slot="sidebar-menu-badge"
      className={cn(
        "absolute right-1",
        "flex h-5 min-w-5",
        "items-center justify-center",
        "rounded-md px-1",
        "text-[10px] font-medium",
        "text-sidebar-foreground/70",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/* Input / Separator                                                         */
/* -------------------------------------------------------------------------- */

export function SidebarInput({
  className,
  ...props
}: React.ComponentProps<"input">) {
  return (
    <input
      data-slot="sidebar-input"
      className={cn(
        "h-8 w-full min-w-0",
        "rounded-md border",
        "border-sidebar-border",
        "bg-sidebar",
        "px-2 text-sm",
        "outline-none",
        "focus-visible:ring-2",
        "focus-visible:ring-sidebar-ring",
        className
      )}
      {...props}
    />
  )
}

export function SidebarSeparator({
  className,
  ...props
}: React.ComponentProps<"div">) {
  return (
    <div
      data-slot="sidebar-separator"
      className={cn(
        "mx-2 h-px bg-sidebar-border",
        className
      )}
      {...props}
    />
  )
}

/* -------------------------------------------------------------------------- */
/* Compatibility primitives                                                  */
/* -------------------------------------------------------------------------- */

export function SidebarRail({
  className,
  ...props
}: React.ComponentProps<"button">) {
  const { toggleSidebar } = useSidebar()

  return (
    <button
      type="button"
      aria-label="Toggle sidebar"
      onClick={toggleSidebar}
      className={cn(
        "absolute inset-y-0 z-20 hidden w-4",
        "translate-x-1/2 md:flex",
        "hover:bg-sidebar-accent/20",
        className
      )}
      {...props}
    />
  )
}

export function SidebarMenuSkeleton({
  className,
  showIcon = false,
  ...props
}: React.ComponentProps<"div"> & {
  showIcon?: boolean
}) {
  return (
    <div
      data-slot="sidebar-menu-skeleton"
      className={cn(
        "flex h-8 items-center gap-2",
        "rounded-md px-2",
        className
      )}
      {...props}
    >
      {showIcon && (
        <div className="size-4 animate-pulse rounded-md bg-muted" />
      )}

      <div className="h-4 flex-1 animate-pulse rounded bg-muted" />
    </div>
  )
}

export function SidebarMenuSub({
  className,
  ...props
}: React.ComponentProps<"ul">) {
  return (
    <ul
      data-slot="sidebar-menu-sub"
      className={cn(
        "mx-3.5 flex min-w-0 flex-col gap-1",
        "border-l border-sidebar-border",
        "px-2.5 py-0.5",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}

export function SidebarMenuSubItem({
  className,
  ...props
}: React.ComponentProps<"li">) {
  return (
    <li
      data-slot="sidebar-menu-sub-item"
      className={cn(
        "group/menu-sub-item relative",
        className
      )}
      {...props}
    />
  )
}

export function SidebarMenuSubButton({
  className,
  isActive = false,
  ...props
}: React.ComponentProps<"a"> & {
  isActive?: boolean
}) {
  return (
    <a
      data-slot="sidebar-menu-sub-button"
      data-active={
        isActive ? "true" : undefined
      }
      className={cn(
        "flex h-7 min-w-0 items-center",
        "gap-2 overflow-hidden",
        "rounded-md px-2",
        "text-xs",
        "text-sidebar-foreground",
        "transition-colors",
        "hover:bg-sidebar-accent",
        "hover:text-sidebar-accent-foreground",
        "data-[active=true]:bg-sidebar-accent",
        "data-[active=true]:text-sidebar-accent-foreground",
        "group-data-[collapsible=icon]:hidden",
        className
      )}
      {...props}
    />
  )
}