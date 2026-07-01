import { useEffect, useState, useRef } from "react";

/**
 * Banner di aggiornamento automatico.
 *
 * Mostra un avviso quando è disponibile una nuova versione.
 * Al click su "Aggiorna" scarica il nuovo binario, riavvia l'app
 * e ricarica il frontend appena il server torna online.
 *
 * USO: importa e metti <UpdateBanner /> in App.jsx o nel layout principale.
 *
 *   import UpdateBanner from "./UpdateBanner";
 *   export default function App() {
 *     return (
 *       <>
 *         <UpdateBanner />
 *         // ... resto dell'app
 *       </>
 *     );
 *   }
 */
export default function UpdateBanner() {
  const [updateInfo, setUpdateInfo] = useState(null); // { version: string }
  const [status, setStatus]         = useState("idle"); // idle | downloading | restarting

  // Controlla update al mount
  useEffect(() => {
    fetch("/api/update/check")
      .then((r) => r.json())
      .then((data) => {
        if (data.available) setUpdateInfo({ version: data.version });
      })
      .catch(() => {}); // silenzioso se il server non risponde
  }, []);

  // Ref per poter pulire il polling anche da un unmount
  const pollRef = useRef(null);

  useEffect(() => {
    // cleanup se il componente smonta mentre sta pollando
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  const handleUpdate = async () => {
    setStatus("downloading");

    try {
      await fetch("/api/update/apply", { method: "POST" });
    } catch {
      // Il server potrebbe chiudersi prima di rispondere — ok
    }

    // Inizia a pollare /api/health ogni 2s
    // Quando il server torna su → ricarica la pagina
    setStatus("restarting");
    pollRef.current = setInterval(() => {
      fetch("/api/health")
        .then(() => {
          clearInterval(pollRef.current);
          window.location.reload();
        })
        .catch(() => {}); // ancora offline, riprova
    }, 2000);
  };

  if (!updateInfo) return null;

  return (
    <div style={styles.banner}>
      <span style={styles.text}>
        {status === "idle" && `🔄 Versione ${updateInfo.version} disponibile`}
        {status === "downloading" && "⏬ Download in corso…"}
        {status === "restarting" && "⚙️ Riavvio in corso… l'app si aggiornerà tra poco"}
      </span>

      {status === "idle" && (
        <button style={styles.button} onClick={handleUpdate}>
          Aggiorna ora
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
