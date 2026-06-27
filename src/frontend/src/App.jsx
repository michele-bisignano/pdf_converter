import { motion } from "motion/react";
import { useState } from "react";
import { Power } from "lucide-react";
import PDFConverterBox from "./components/PDFConverterBox";

function ShutdownButton() {
  const [shutting, setShutting] = useState(false);

  const handleShutdown = async () => {
    setShutting(true);
    try {
      await fetch("/api/shutdown", { method: "POST" });
    } catch {
      // Server may close before responding
    }
  };

  return (
    <button
      onClick={handleShutdown}
      disabled={shutting}
      className="fixed top-4 right-4 z-[10000] flex items-center gap-1.5 px-3 py-1.5 rounded-full glass text-zinc-400 hover:text-red-400 hover:border-red-500/30 text-xs transition-colors duration-200 disabled:opacity-50"
      title={shutting ? "Shutting down..." : "Exit application"}
    >
      <Power className="w-3.5 h-3.5" />
      {shutting ? "Closing..." : "Exit"}
    </button>
  );
}

const FEATURES = [
  {
    id: "pdf-to-excel",
    title: "PDF → Excel",
    description: "",
    icon: "📄",
    component: PDFConverterBox,
  },
];

export default function App() {
  return (
    <div className="min-h-screen p-4 md:p-8 flex flex-col items-center">
      <ShutdownButton />
      <header className="mb-12 mt-8 text-center">
        <motion.h1
          className="text-5xl md:text-7xl font-black tracking-tighter text-gradient"
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
        >
          PDF Converter
        </motion.h1>
      </header>

      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
        {FEATURES.map((feature, i) => (
          <motion.div
            key={feature.id}
            className="glass rounded-3xl p-6 md:p-8 col-span-2 row-span-2 relative group overflow-hidden"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: 0.4 + 0.1 * i, duration: 0.5 }}
          >
            <feature.component />
          </motion.div>
        ))}
      </div>

      <footer className="mt-auto pt-12 pb-6 text-zinc-600 text-xs text-center">
        pdf_converter v2.0.0
      </footer>
    </div>
  );
}
