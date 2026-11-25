import { CATEGORY_META } from "../categories";
import type { CareTask } from "../types";
import { formatRelative, formatTime } from "../time";

interface Props {
  task: CareTask;
  section: "overdue" | "due" | "done";
  now: Date;
  onComplete: (taskId: string) => void;
  completing: boolean;
  canComplete: boolean;
}

export default function TaskCard({ task, section, now, onComplete, completing, canComplete }: Props) {
  const meta = CATEGORY_META[task.category];

  return (
    <div className={`task-card task-card--${section}`}>
      <div className="task-card__main">
        <span className="task-card__icon" aria-hidden="true">
          {meta.icon}
        </span>
        <div className="task-card__text">
          <div className="task-card__title">{task.title}</div>
          <div className="task-card__meta">
            {meta.label} &middot; due {formatTime(task.due_at)}
            {section === "overdue" && <span className="task-card__overdue-tag"> &middot; {formatRelative(task.due_at, now)}</span>}
          </div>
          {task.notes && <div className="task-card__notes">{task.notes}</div>}
          {section === "done" && task.completed_by && task.completed_at && (
            <div className="task-card__done-by">
              ✓ {task.completed_by.name} at {formatTime(task.completed_at)}
            </div>
          )}
        </div>
      </div>

      {section !== "done" && (
        <button
          type="button"
          className="task-card__complete-btn"
          onClick={() => onComplete(task.id)}
          disabled={completing || !canComplete}
          title={canComplete ? "Mark as done" : "Choose your name above first"}
        >
          {completing ? "Saving…" : "Mark done"}
        </button>
      )}
    </div>
  );
}
