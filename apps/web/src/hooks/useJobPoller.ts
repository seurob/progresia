import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import { JobStatus } from "../types/api";

type PollState = "idle" | "polling" | "completed" | "failed";

const MAX_POLLS = 150; // 5 min at 2s intervals

export function useJobPoller(onComplete: () => void) {
  const [jobId, setJobId] = useState<string | null>(null);
  const [state, setState] = useState<PollState>("idle");
  const [error, setError] = useState<string | null>(null);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const pollCountRef = useRef(0);

  function startPolling(id: string) {
    pollCountRef.current = 0;
    setJobId(id);
    setState("polling");
    setError(null);
  }

  useEffect(() => {
    if (state !== "polling" || !jobId) return;

    intervalRef.current = setInterval(async () => {
      pollCountRef.current += 1;

      if (pollCountRef.current > MAX_POLLS) {
        clearInterval(intervalRef.current!);
        setState("failed");
        setError("El job no completó en 5 minutos");
        return;
      }

      try {
        const res = await api.get<JobStatus>(`/jobs/${jobId}`);
        const { status } = res.data;
        if (status === "completed") {
          clearInterval(intervalRef.current!);
          setState("completed");
          onComplete();
        } else if (status === "failed") {
          clearInterval(intervalRef.current!);
          setState("failed");
          setError(res.data.failReason ?? "Job failed");
        }
      } catch {
        clearInterval(intervalRef.current!);
        setState("failed");
        setError("Could not poll job status");
      }
    }, 2000);

    return () => clearInterval(intervalRef.current!);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [jobId, state]);

  function reset() {
    clearInterval(intervalRef.current!);
    setJobId(null);
    setState("idle");
    setError(null);
  }

  return {
    isPolling: state === "polling",
    isCompleted: state === "completed",
    isFailed: state === "failed",
    error,
    startPolling,
    reset
  };
}
