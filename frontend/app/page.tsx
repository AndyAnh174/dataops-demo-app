"use client";

import { useEffect, useState } from "react";


type Health = {
  status: "ok";
  service: string;
  revision: string;
};

type DemoMessage = {
  message: string;
};

type DemoState = {
  health: Health | null;
  message: string;
  loading: boolean;
};

const initialState: DemoState = {
  health: null,
  message: "Connecting to the FastAPI service…",
  loading: true,
};

async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(path, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export default function Home() {
  const [state, setState] = useState<DemoState>(initialState);

  useEffect(() => {
    let active = true;

    Promise.all([
      fetchJson<Health>("/api/health"),
      fetchJson<DemoMessage>("/api/message"),
    ])
      .then(([health, message]) => {
        if (active) {
          setState({ health, message: message.message, loading: false });
        }
      })
      .catch(() => {
        if (active) {
          setState({
            health: null,
            message: "The API did not answer. Check the deployment workflow.",
            loading: false,
          });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  const online = state.health?.status === "ok";

  return (
    <main>
      <section className="hero">
        <p className="eyebrow">LIVE DELIVERY LAB</p>
        <h1>DataOps Demo</h1>
        <p className="lede">
          A Next.js frontend and FastAPI backend, tested and deployed from GitHub by a
          self-hosted runner.
        </p>

        <div className="statusCard" aria-live="polite">
          <div>
            <span className="label">API status</span>
            <strong className={online ? "online" : "offline"}>
              {state.loading ? "Checking…" : online ? "Online" : "Unavailable"}
            </strong>
          </div>
          <div>
            <span className="label">Revision</span>
            <code>{state.health?.revision ?? "—"}</code>
          </div>
          <div className="message">
            <span className="label">Runtime message</span>
            <p>{state.message}</p>
          </div>
        </div>

        <div className="flow" aria-label="Deployment flow">
          <span>Git push</span><i>→</i><span>CI tests</span><i>→</i><span>Deploy</span><i>→</i><span>DataOps event</span>
        </div>
      </section>
    </main>
  );
}
