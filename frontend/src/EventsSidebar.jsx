/* ─── Sidebar root wrapper ──────────────────────────────────────── */
 
.ec - root {
    display: flex;
    flex - shrink: 0;
    position: relative;
}
 
.ec - root--open.ec - sidebar {
    width: 220px;
    opacity: 1;
}
 
.ec - root--closed.ec - sidebar {
    width: 0;
    opacity: 0;
    pointer - events: none;
}

/* ─── Sidebar panel ─────────────────────────────────────────────── */
 
.ec - sidebar {
    overflow: hidden;
    display: flex;
    flex - direction: column;
    border - right: 1px solid rgba(255, 255, 255, 0.06);
    background: rgba(255, 255, 255, 0.015);
    transition: width 0.22s cubic - bezier(0.4, 0, 0.2, 1),
        opacity 0.18s ease;
    will - change: width;
}
 
.ec - sidebar - header {
    display: flex;
    align - items: center;
    justify - content: space - between;
    padding: 16px 14px 10px;
    flex - shrink: 0;
    border - bottom: 1px solid rgba(255, 255, 255, 0.05);
    min - width: 220px;
}
 
.ec - sidebar - title {
    font - family: var(--font - mono, "JetBrains Mono", monospace);
    font - size: 10px;
    font - weight: 500;
    letter - spacing: 0.1em;
    color: var(--text - dim, rgba(255, 255, 255, 0.35));
}
 
.ec - sidebar - body {
    flex: 1;
    overflow - y: auto;
    overflow - x: hidden;
    padding: 8px 8px;
    min - width: 220px;
    scrollbar - width: thin;
    scrollbar - color: rgba(255, 255, 255, 0.08) transparent;
}
 
.ec - sidebar - body:: -webkit - scrollbar {
    width: 3px;
}
 
.ec - sidebar - body:: -webkit - scrollbar - thumb {
    background: rgba(255, 255, 255, 0.08);
    border - radius: 2px;
}
 
.ec - footer {
    font - family: var(--font - mono, "JetBrains Mono", monospace);
    font - size: 10px;
    color: var(--text - dim, rgba(255, 255, 255, 0.25));
    padding: 8px 14px 12px;
    min - width: 220px;
    border - top: 1px solid rgba(255, 255, 255, 0.04);
}