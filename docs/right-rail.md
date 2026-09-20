---
title: Right Rail (research sidebar) — design & implementation
updated: 2026-09-20
tags: [frontend, layout, shadcn, sidebar]
status: current
---

# Right Rail — design & implementation

The right-hand research panel (News / Graphs / Anomalies) is built on
shadcn's Base UI `Sidebar` primitive
(https://ui.shadcn.com/docs/components/base/sidebar), customized into an
overlay drawer with an always-visible icon strip and accordion sections.

> **Vault note:** this belongs in
> `obsidian vault\stock_project\`, not here. It's parked in
> `stock_research\docs\` because that Obsidian folder isn't currently in the
> filesystem MCP server's allowed directories (only `rustgo project`,
> `rust_pro`, and `stock_research` are exposed). Move it once that's fixed.

---

## 1. Requirements

1. Collapsed state shows an icon-only tab strip (News / Graphs / Anomalies).
2. That strip is **always visible on desktop**; on mobile it's icon-only too
   (no labels), and the full panel opens as a sheet.
3. News / Graphs / Anomalies are **accordion/dropdown sections** — one open
   at a time — not a flat tab switch.
4. The open/close transition has a **backdrop blur**, identical on mobile
   and desktop.

---

## 2. Key decision: overlay drawer, not shadcn's default push drawer

shadcn's `collapsible="icon"` normally **reflows the page** when the sidebar
expands: the in-flow `sidebar-gap` element grows from `--sidebar-width-icon`
to `--sidebar-width`, and the fixed panel follows it in lockstep.

That's wrong for this use case:
- The chat column would re-wrap on every toggle.
- A push layout has no "behind" for a blur scrim to sit in on desktop —
  ruling out requirement 4 for that breakpoint.

**Decision:** decouple the in-flow gap from the panel's visual width.

- `--sidebar-width` **and** `--sidebar-width-icon` are both pinned to
  `3.5rem` on `SidebarProvider`. The in-flow gap is therefore a constant
  3.5rem in every state — the chat never reflows.
- A separate `--rail-width` (`min(22rem, 92vw)`) grows only the *fixed*
  panel container, via `group-data-[state=expanded]:w-(--rail-width)` on
  `<Sidebar>`.
- A scrim (`fixed inset-0 bg-black/45 backdrop-blur-md`) sits behind the
  panel on desktop; on mobile the same effect comes from the sheet's own
  backdrop, retuned to matching values.

Net effect: the rail behaves like a floating overlay drawer identically on
both breakpoints — panel slides in, background blurs, content underneath
never moves.

---

## 3. Architecture

```
SidebarProvider                         (AppLayout — top-level, owns viewport)
├── RailProvider                        (shared section/open state)
│   ├── SidebarInset                    (Header + chat column)
│   │   └── RailIconStrip (md:hidden)   (in-flow icon column, mobile only)
│   └── RightRail
│       ├── desktop scrim (md:block)    (fixed, blurred, click-to-close)
│       └── Sidebar (side="right", collapsible="icon")
│           ├── SidebarHeader            (label + trigger)
│           ├── SidebarContent
│           │   ├── collapsed icon menu  (group-data-[collapsible=icon]:block)
│           │   └── accordion            (group-data-[collapsible=icon]:hidden)
│           │       └── SidebarGroup × 3 (News / Graphs / Anomalies)
│           │           ├── SidebarGroupLabel as <button>  (header, chevron)
│           │           └── motion.div > SidebarGroupContent  (open panel only)
│           └── SidebarFooter            (keyboard hint)
```

### Section state — `layouts/rail/rail-context.tsx`
Single source of truth for the three sections (`id`, `label`, `icon`),
consumed by the mobile strip, the desktop collapsed icon menu, and the
accordion headers alike. `RailProvider` must be mounted inside
`SidebarProvider` (it reads `useSidebar()`) and exposes:

- `section` — which accordion panel is open (`null` = collapsed)
- `toggleSection(id)` — accordion behaviour (click open section → closes it)
- `openSection(id)` — icon-strip behaviour: select + open the rail,
  branching on `isMobile` to call `setOpenMobile` or `setOpen`
- `closeRail()` — used after an action (e.g. picking an anomaly) hands the
  screen back to the chat

### Icon strip in both breakpoints
| State | Desktop | Mobile |
|---|---|---|
| Closed | collapsed sidebar **is** the icon menu (3.5rem, `collapsible="icon"`) | `RailIconStrip` — a separate in-flow 3rem column |
| Open | 22rem panel over a blurred scrim | sheet at `--sidebar-width-mobile` |

`RailIconStrip` (`layouts/rail/RailIconStrip.tsx`) is deliberately **in-flow**
(a flex sibling of the chat column), not `position: fixed` — it then sits
under the header automatically and can never cover content, unlike a fixed
overlay would. It only renders on mobile (`md:hidden`) because on desktop
the collapsed sidebar already serves as the strip.

### Accordion, not `Collapsible`
Each section header is a `SidebarGroupLabel` rendered as a `<button>`
(`aria-expanded`, `aria-controls`, rotating `ChevronDown`) — the pattern the
shadcn docs use for collapsible groups. The **body** is deliberately *not*
wrapped in shadcn's `Collapsible` primitive: `Collapsible` animates
`height`, which fights panels that are themselves scroll containers needing
to fill the remaining rail height on open. Instead:

- open group → `flex-1`, closed groups → `flex-none` (flex resolves the
  height in a single frame)
- the panel body fades in via a small `framer-motion` wrapper
  (`opacity`/`y`, 220ms) — motion carries the perceived transition, flex
  does the layout work

Height chain that must stay unbroken end-to-end (each panel renders
`h-full` + its own `overflow-y-auto`):

```
sidebar-inner (flex-col, size-full)
  → SidebarContent (flex-1 min-h-0, overflow-hidden)
    → SidebarGroup (flex-1 min-h-0)
      → motion.div (flex-1 min-h-0 overflow-hidden)
        → SidebarGroupContent (h-full)
          → panel (h-full, own scroll)
```

---

## 4. Blur / glass — matching mobile and desktop

| Surface | Before | After |
|---|---|---|
| Desktop scrim | *(none)* | new: `fixed inset-0 z-30 bg-black/45 backdrop-blur-md`, kept mounted and faded via opacity (not conditionally rendered) so the blur *animates* rather than popping in |
| Mobile sheet backdrop (`sheet.tsx`) | `bg-black/10`, 150ms, `blur-xs` (only if `supports-backdrop-filter`) | `bg-black/45 backdrop-blur-md`, 300ms — matches the desktop scrim exactly |
| Sidebar panel surface (`sidebar.tsx`, desktop) | opaque `bg-[var(--bg)]` | `bg-[var(--sidebar-glass)] backdrop-blur-xl` — was opaque, so no blur would ever have been visible through it regardless of the scrim |
| Sidebar panel surface (`sidebar.tsx`, mobile sheet) | `bg-sidebar` (opaque) | same `bg-[var(--sidebar-glass)] backdrop-blur-xl` |

`--sidebar-glass` (`rgba(36, 33, 29, 0.82)`) is defined on `:root` in
`index.css`, **not** on `SidebarProvider` — the mobile sheet is rendered
through a React portal to `<body>`, so it never inherits custom properties
set on the provider element. `--sidebar-width-mobile` lives there for the
same reason.

---

## 5. Files touched

| File | Role |
|---|---|
| `layouts/AppLayout.tsx` | `SidebarProvider` at viewport root, sizing vars (`--sidebar-width`, `--sidebar-width-icon`, `--rail-width`), mounts `RailProvider`, places `RailIconStrip` |
| `layouts/RightRail.tsx` | the rail itself: scrim, collapsed icon menu, accordion sections, footer |
| `layouts/rail/rail-context.tsx` | `RAIL_SECTIONS` list + `RailProvider`/`useRail()` shared state |
| `layouts/rail/RailIconStrip.tsx` | mobile in-flow icon strip |
| `layouts/Header.tsx` | trigger button; reads `isMobile ? openMobile : open` (not just `open`, which is desktop-only state) |
| `components/ui/sidebar.tsx` | glass surfaces (desktop + mobile), mobile width honoring `--sidebar-width-mobile`, fixed a props-spread bug on the mobile `Sheet` |
| `components/ui/sheet.tsx` | backdrop blur/darkness/timing brought in line with the desktop scrim |
| `index.css` | `@theme inline` bridge (Tailwind v4 doesn't read `tailwind.config.js`), `--sidebar-glass`, `--sidebar-width-mobile` |

---

## 6. Known follow-ups

- `dark:` Tailwind variants in the shadcn components are currently inert —
  v4's default `dark:` is `prefers-color-scheme`, and `.dark` is never
  applied to `<html>` (dark values are hardcoded straight into `:root`
  instead). Cosmetic only; not fixed.
- `SidebarMenuButton`'s `tooltip` prop (used in the collapsed icon menu) is
  the first use of that prop in this codebase — routes through Base UI's
  `useRender` + `TooltipTrigger`. Worth a visual check; fallback if it
  misbehaves is a plain `title={label}`.
- This doc belongs in `obsidian vault\stock_project\` — move once that
  folder is added to the filesystem MCP server's allowed directories.
