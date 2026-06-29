import { motion } from "motion/react";
import { useState, useEffect, useRef } from "react";
import { Power } from "lucide-react";
import PDFConverterBox from "./components/PDFConverterBox";
import UpdateBanner from "./components/UpdateBanner";
import { sendHeartbeat, requestShutdown } from "./services/api";

const HEARTBEAT_INTERVAL_MS = 5000;

/**
 * Keeps the backend's watchdog informed that this tab is still open.
 * Sends a heartbeat immediately and then on a fixed interval for as
 * long as the component is mounted. If the tab closes (or the process
 * is killed) the interval simply stops -- no cleanup call needed.
 *
 * @returns {null} Renders nothing; side-effect-only component
 */
function HeartbeatPulse() {
  useEffect(() => {
    sendHeartbeat();
    const id = setInterval(sendHeartbeat, HEARTBEAT_INTERVAL_MS);
    return () => clearInterval(id);
  }, []);

  return null;
}

/**
 * Shutdown button that asks the backend to gracefully stop the server.
 *
 * Uses navigator.sendBeacon (via requestShutdown) instead of fetch,
 * since sendBeacon is guaranteed by the browser to be delivered even
 * if the tab is closed immediately after. A short confirmation step
 * avoids accidental clicks, and the button explains that the browser
 * tab itself should be closed manually afterwards -- most browsers
 * don't allow scripts to close tabs they didn't open themselves.
 *
 * @returns {JSX.Element} A floating button in the top-right corner
 */
function ShutdownButton() {
  const [confirming, setConfirming] = useState(false);
  const [stopped, setStopped] = useState(false);
  const timeoutRef = useRef(null);

  useEffect(() => () => clearTimeout(timeoutRef.current), []);

  const handleClick = () => {
    if (!confirming) {
      setConfirming(true);
      timeoutRef.current = setTimeout(() => setConfirming(false), 4000);
      return;
    }
    clearTimeout(timeoutRef.current);
    requestShutdown();
    setStopped(true);
  };

  return (
    <motion.button
      onClick={handleClick}
      disabled={stopped}
      className={`fixed top-4 right-4 z-[10000] flex items-center gap-2 px-3 py-2
        overflow-hidden rounded-full border text-xs transition-colors duration-300
        disabled:opacity-50 group ${
          confirming
            ? "border-red-500/40 bg-red-500/10 text-red-400"
            : "border-white/10 bg-white/[0.03] text-zinc-400 hover:text-red-400"
        }`}
      whileHover={{ scale: 1.05 }}
      whileTap={{ scale: 0.95 }}
      title={
        stopped
          ? "Server stopped — you can close this tab"
          : confirming
            ? "Click again to confirm"
            : "Stop server"
      }
    >
      <span className="absolute inset-0 bg-gradient-to-r from-transparent via-white/[0.08] to-transparent
        opacity-0 transition-opacity duration-500 group-hover:opacity-100
        group-hover:animate-shimmer pointer-events-none" />
      <Power className="w-3.5 h-3.5 relative z-10" />
      <span className="relative z-10">
        {stopped ? "You can close this tab" : confirming ? "Confirm?" : "Exit"}
      </span>
    </motion.button>
  );
}

const FEATURES = [
  {
    id: "pdf-to-excel",
    title: "PDF to Excel",
    description: "",
    icon: "page_facing_up",
    component: PDFConverterBox,
  },
];

/**
 * Root application component.
 *
 * Renders the page header, the feature card containing the
 * PDF converter, a shutdown button, and a footer.
 *
 * @returns {JSX.Element} The full application layout
 */
export default function App() {
  return (
    <div className="min-h-screen p-4 md:p-8 flex flex-col items-center">
      <HeartbeatPulse />
      <UpdateBanner />
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
