export const PRIVACY_PATH = "/privacy";

/**
 * Site-wide footer. Rendered by AppLayout so it appears on every page of the
 * app; the standalone privacy page renders it too.
 *
 * Plain <a> (full navigation) on purpose: the app has no client-side router and
 * the policy is a separate, rarely-visited page.
 */
export default function Footer() {
  return (
    <footer className="flex shrink-0 items-center justify-center gap-2 px-3 pb-3 pt-1 font-mono text-[11px] text-[var(--text-dim)] md:px-6">
      <span>© {new Date().getFullYear()} Market Mind</span>
      <span aria-hidden="true">·</span>
      <a
        href={PRIVACY_PATH}
        className="rounded-sm underline-offset-4 transition-colors hover:text-[var(--text)] hover:underline focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[var(--amber)]/60"
      >
        Privacy Policy
      </a>
    </footer>
  );
}
