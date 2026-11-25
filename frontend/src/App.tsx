import { useCallback, useEffect, useState } from "react";
import { ApiError, completeTask, getFamilyMembers, getRecipients, getToday } from "./api";
import AddTaskForm from "./components/AddTaskForm";
import AskAssistant from "./components/AskAssistant";
import TodayScreen from "./components/TodayScreen";
import WhoAmI from "./components/WhoAmI";
import type { CareRecipient, FamilyMember, TodayResponse } from "./types";

const WHOAMI_KEY = "carecircle.whoami";

export default function App() {
  const [recipient, setRecipient] = useState<CareRecipient | null>(null);
  const [members, setMembers] = useState<FamilyMember[]>([]);
  const [today, setToday] = useState<TodayResponse | null>(null);
  const [whoAmIId, setWhoAmIId] = useState<string | null>(() => localStorage.getItem(WHOAMI_KEY));
  const [completingId, setCompletingId] = useState<string | null>(null);
  const [now, setNow] = useState(() => new Date());
  const [loading, setLoading] = useState(true);
  const [notice, setNotice] = useState<string | null>(null);
  const [fatalError, setFatalError] = useState<string | null>(null);

  const refreshToday = useCallback(async (recipientId: string) => {
    const data = await getToday(recipientId);
    setToday(data);
    setNow(new Date());
  }, []);

  useEffect(() => {
    (async () => {
      try {
        const recipients = await getRecipients();
        const first = recipients[0];
        if (!first) {
          setFatalError("No care recipient set up yet.");
          return;
        }
        setRecipient(first);
        const [memberList] = await Promise.all([getFamilyMembers(), refreshToday(first.id)]);
        setMembers(memberList);
      } catch (err) {
        setFatalError(err instanceof Error ? err.message : "Could not load CareCircle");
      } finally {
        setLoading(false);
      }
    })();
  }, [refreshToday]);

  useEffect(() => {
    if (!recipient) return;
    const interval = setInterval(() => refreshToday(recipient.id), 60_000);
    return () => clearInterval(interval);
  }, [recipient, refreshToday]);

  useEffect(() => {
    if (whoAmIId) localStorage.setItem(WHOAMI_KEY, whoAmIId);
  }, [whoAmIId]);

  async function handleComplete(taskId: string) {
    if (!recipient || !whoAmIId) return;
    setCompletingId(taskId);
    setNotice(null);
    try {
      await completeTask(taskId, whoAmIId);
    } catch (err) {
      if (err instanceof ApiError && err.status === 409) {
        setNotice("Someone else just marked that done a moment ago.");
      } else {
        setNotice(err instanceof Error ? err.message : "Could not update the task");
      }
    } finally {
      await refreshToday(recipient.id);
      setCompletingId(null);
    }
  }

  if (loading) {
    return <div className="app-loading">Loading CareCircle…</div>;
  }

  if (fatalError || !recipient) {
    return <div className="app-loading">{fatalError ?? "Something went wrong."}</div>;
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>CareCircle Lite</h1>
        <p className="app-header__recipient">Caring for {recipient.name}</p>
        <WhoAmI members={members} selectedId={whoAmIId} onChange={setWhoAmIId} />
      </header>

      {notice && <div className="app-notice">{notice}</div>}

      <main className="app-main">
        <AddTaskForm
          recipientId={recipient.id}
          whoAmIId={whoAmIId}
          onCreated={() => refreshToday(recipient.id)}
        />

        {today && (
          <TodayScreen
            data={today}
            now={now}
            onComplete={handleComplete}
            completingId={completingId}
            canComplete={!!whoAmIId}
          />
        )}

        <AskAssistant recipientId={recipient.id} />
      </main>
    </div>
  );
}
