import { motion } from "motion/react";
import PDFConverterBox from "./components/PDFConverterBox";

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
