import { motion } from "framer-motion";

interface HeaderProps {
  stocksTracked: number;
}

export default function Header({ stocksTracked }: HeaderProps) {
  return (
    <header className="relative z-[1200] flex shrink-0 items-center justify-between border-b border-[var(--border)] px-3 py-3.5 md:px-6 md:py-[18px]">
      <div className="flex min-w-0 items-center">
        <div className="flex items-center gap-2.5">
          <motion.div
            initial={{ scale: 0.92, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            transition={{ duration: 0.3, ease: "easeOut" }}
            className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-[var(--amber)] font-mono text-[13px] font-medium tracking-[-0.5px] text-[#080c10]"
          >
            M²
          </motion.div>
          <span className="truncate text-[15px] font-semibold tracking-[-0.3px] text-[var(--text)]">
            Market Mind
          </span>
        </div>
      </div>

      <div className="flex shrink-0 items-center gap-1.5 font-mono text-[10px] text-[var(--text-muted)] md:text-[11px]">
        <motion.span
          aria-hidden="true"
          animate={{ opacity: [1, 0.4, 1] }}
          transition={{ duration: 2, repeat: Infinity, ease: "easeInOut" }}
          className="h-1.5 w-1.5 rounded-full bg-[var(--green)]"
        />
        <span>{stocksTracked} STOCKS TRACKED</span>
      </div>
    </header>
  );
}
