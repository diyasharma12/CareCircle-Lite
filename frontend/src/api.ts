import type { CareRecipient, CareTask, FamilyMember, TaskCategory, TodayResponse } from "./types";

const BASE_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new ApiError(res.status, body.detail ?? `Request failed: ${res.status}`);
  }
  return res.json();
}

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
  }
}

export function getRecipients(): Promise<CareRecipient[]> {
  return request("/recipients");
}

export function getFamilyMembers(): Promise<FamilyMember[]> {
  return request("/family-members");
}

export function getToday(recipientId: string): Promise<TodayResponse> {
  return request(`/tasks/today?recipient_id=${encodeURIComponent(recipientId)}`);
}

export interface NewTaskInput {
  recipient_id: string;
  title: string;
  category: TaskCategory;
  due_at: string;
  notes?: string;
  created_by_id?: string;
}

export function createTask(payload: NewTaskInput): Promise<CareTask> {
  return request("/tasks", { method: "POST", body: JSON.stringify(payload) });
}

export function completeTask(taskId: string, completedById: string): Promise<CareTask> {
  return request(`/tasks/${taskId}/complete`, {
    method: "POST",
    body: JSON.stringify({ completed_by_id: completedById }),
  });
}

export interface AskHandlers {
  onChunk: (text: string) => void;
  onDone: (latencyMs: number) => void;
  onError: (message: string) => void;
}

/**
 * Streams the assistant's answer via SSE. fetch + ReadableStream is used
 * instead of EventSource because EventSource can't send a JSON POST body.
 */
export async function askAssistant(
  recipientId: string,
  question: string,
  handlers: AskHandlers
): Promise<void> {
  try {
    const res = await fetch(`${BASE_URL}/assistant/ask`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ recipient_id: recipientId, question }),
    });
    if (!res.ok || !res.body) {
      throw new Error(`Assistant request failed: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      const events = buffer.split("\n\n");
      buffer = events.pop() ?? "";

      for (const event of events) {
        const line = event.split("\n").find((l) => l.startsWith("data: "));
        if (!line) continue;
        const data = JSON.parse(line.slice("data: ".length));
        if (data.chunk) handlers.onChunk(data.chunk);
        if (data.done) handlers.onDone(data.latency_ms);
      }
    }
  } catch (err) {
    handlers.onError(err instanceof Error ? err.message : "Something went wrong");
  }
}
