import { useEffect, useState } from "react";

/**
 * Auto-update banner.
 *
 * Shows a notification when a new version is available.
 * On click "Update" downloads the new binary, restarts the app
 * and reloads the frontend once the server comes back online.
 *
 * USAGE: import and place <UpdateBanner /> in App.jsx or the main layout.
 *
 *   import UpdateBanner from "./UpdateBanner";
 *   export default function App() {
 *     return (
 *       <>
 *         <UpdateBanner />
 *         // ... rest of the app
 *       </>
 *     );
 *   }
 */
export default function UpdateBanner() {
  const [updateInfo, setUpdateInfo] = useState(null); // { version: string }
  const [status, setStatus]         = useState("idle"); // idle | downloading | restarting

  // Check for updates on mount
  useEffect(() => {
    fetch("/api/update/check")
      .then((r) => r.json())
      .then((data) => {
        if (data.available) setUpdateInfo({ version: data.version });
      })
      .catch(() => {}); // silent if server does not respond
  }, []);

  const handleUpdate = async () => {
    setStatus("downloading");

    try {
      await fetch("/api/update/apply", { method: "POST" });
    } catch {
      // Server may close before responding — ok
    }

    // Start polling /api/health every 2s
    // When the server is back up -> reload the page
    setStatus("restarting");
    const poll = setInterval(() => {
      fetch("/api/health")
        .then(() => {
          clearInterval(poll);
          window.location.reload();
        })
        .catch(() => {}); // still offline, retry
    }, 2000);
  };

  if (!updateInfo) return null;

  return (
    <div style={styles.banner}>
      <span style={styles.text}>
        {status === "idle" && `🔄 Version ${updateInfo.version} available`}
        {status === "downloading" && "⏬ Downloading…"}
        {status === "restarting" && "⚙️ Restarting… the app will update shortly"}
      </span>

      {status === "idle" && (
        <button style={styles.button} onClick={handleUpdate}>
          Update now
        </button>
      )}
    </div>
  );
}

const styles = {
  banner: {
    display:         "flex",
    alignItems:      "center",
    justifyContent:  "space-between",
    padding:         "10px 20px",
    background:      "#fbbf24",
    color:           "#1c1917",
    fontFamily:      "sans-serif",
    fontSize:        "14px",
    position:        "sticky",
    top:             0,
    zIndex:          9999,
    boxShadow:       "0 2px 6px rgba(0,0,0,0.15)",
  },
  text: {
    fontWeight: 500,
  },
  button: {
    background:   "#1c1917",
    color:        "#fff",
    border:       "none",
    borderRadius: "6px",
    padding:      "6px 16px",
    cursor:       "pointer",
    fontWeight:   600,
    fontSize:     "13px",
  },
};
