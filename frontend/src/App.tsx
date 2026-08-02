import { motion } from "framer-motion";

function App() {
  return (
    <main className="flex min-h-screen items-center justify-center bg-zinc-950 px-6 text-white">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.5 }}
        className="rounded-2xl border border-white/10 bg-white/5 p-10 text-center shadow-2xl backdrop-blur-xl"
      >
        <p className="mb-3 text-sm font-medium uppercase tracking-[0.25em] text-amber-400">
          Market Mind
        </p>

        <h1 className="text-4xl font-bold tracking-tight">
          React + TypeScript
        </h1>

        <p className="mt-3 text-zinc-400">
          Tailwind CSS + Framer Motion are working.
        </p>

        <motion.div
          className="mx-auto mt-8 h-3 w-3 rounded-full bg-amber-400"
          animate={{
            scale: [1, 1.5, 1],
            opacity: [1, 0.5, 1],
          }}
          transition={{
            duration: 1.2,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      </motion.div>
    </main>
  );
}

export default App;