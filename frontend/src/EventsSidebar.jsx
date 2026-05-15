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