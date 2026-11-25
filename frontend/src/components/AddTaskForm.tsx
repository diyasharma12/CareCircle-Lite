import { useState } from "react";
import { createTask } from "../api";
import { CATEGORY_META } from "../categories";
import { toLocalDateTimeInputValue } from "../time";
import type { TaskCategory } from "../types";

interface Props {
  recipientId: string;
  whoAmIId: string | null;
  onCreated: () => void;
}

const CATEGORIES = Object.keys(CATEGORY_META) as TaskCategory[];

export default function AddTaskForm({ recipientId, whoAmIId, onCreated }: Props) {
  const [open, setOpen] = useState(false);
  const [title, setTitle] = useState("");
  const [category, setCategory] = useState<TaskCategory>("medicine");
  const [dueAt, setDueAt] = useState(() => toLocalDateTimeInputValue(new Date()));
  const [notes, setNotes] = useState("");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function reset() {
    setTitle("");
    setCategory("medicine");
    setDueAt(toLocalDateTimeInputValue(new Date()));
    setNotes("");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!title.trim()) return;
    setSaving(true);
    setError(null);
    try {
      await createTask({
        recipient_id: recipientId,
        title: title.trim(),
        category,
        due_at: new Date(dueAt).toISOString(),
        notes: notes.trim() || undefined,
        created_by_id: whoAmIId ?? undefined,
      });
      reset();
      setOpen(false);
      onCreated();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not add the task");
    } finally {
      setSaving(false);
    }
  }

  if (!open) {
    return (
      <button type="button" className="add-task-toggle" onClick={() => setOpen(true)}>
        + Add a task
      </button>
    );
  }

  return (
    <form className="add-task-form" onSubmit={handleSubmit}>
      <div className="add-task-form__row">
        <label htmlFor="task-title">What needs doing?</label>
        <input
          id="task-title"
          type="text"
          placeholder="e.g. Evening BP tablet"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          required
          autoFocus
        />
      </div>

      <div className="add-task-form__row add-task-form__row--split">
        <div>
          <label htmlFor="task-category">Type</label>
          <select
            id="task-category"
            value={category}
            onChange={(e) => setCategory(e.target.value as TaskCategory)}
          >
            {CATEGORIES.map((c) => (
              <option key={c} value={c}>
                {CATEGORY_META[c].icon} {CATEGORY_META[c].label}
              </option>
            ))}
          </select>
        </div>
        <div>
          <label htmlFor="task-due">Due</label>
          <input
            id="task-due"
            type="datetime-local"
            value={dueAt}
            onChange={(e) => setDueAt(e.target.value)}
            required
          />
        </div>
      </div>

      <div className="add-task-form__row">
        <label htmlFor="task-notes">Notes (optional)</label>
        <input
          id="task-notes"
          type="text"
          placeholder="e.g. Confirm with Dr. Rao's clinic"
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      {error && <p className="add-task-form__error">{error}</p>}

      <div className="add-task-form__actions">
        <button type="submit" className="add-task-form__save" disabled={saving}>
          {saving ? "Adding…" : "Add task"}
        </button>
        <button type="button" className="add-task-form__cancel" onClick={() => setOpen(false)}>
          Cancel
        </button>
      </div>
    </form>
  );
}
