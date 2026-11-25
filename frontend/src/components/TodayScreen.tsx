import type { CareTask, TodayResponse } from "../types";
import TaskCard from "./TaskCard";

interface Props {
  data: TodayResponse;
  now: Date;
  onComplete: (taskId: string) => void;
  completingId: string | null;
  canComplete: boolean;
}

function Section({
  title,
  tasks,
  section,
  emptyMessage,
  now,
  onComplete,
  completingId,
  canComplete,
}: {
  title: string;
  tasks: CareTask[];
  section: "overdue" | "due" | "done";
  emptyMessage: string;
  now: Date;
  onComplete: (taskId: string) => void;
  completingId: string | null;
  canComplete: boolean;
}) {
  return (
    <section className={`today-section today-section--${section}`}>
      <h2 className="today-section__heading">
        {title} <span className="today-section__count">{tasks.length}</span>
      </h2>
      {tasks.length === 0 ? (
        <p className="today-section__empty">{emptyMessage}</p>
      ) : (
        <div className="today-section__list">
          {tasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              section={section}
              now={now}
              onComplete={onComplete}
              completing={completingId === task.id}
              canComplete={canComplete}
            />
          ))}
        </div>
      )}
    </section>
  );
}

export default function TodayScreen({ data, now, onComplete, completingId, canComplete }: Props) {
  return (
    <div className="today-screen">
      <Section
        title="Overdue"
        tasks={data.overdue}
        section="overdue"
        emptyMessage="Nothing overdue. Nice work!"
        now={now}
        onComplete={onComplete}
        completingId={completingId}
        canComplete={canComplete}
      />
      <Section
        title="Due today"
        tasks={data.due}
        section="due"
        emptyMessage="No more tasks due today."
        now={now}
        onComplete={onComplete}
        completingId={completingId}
        canComplete={canComplete}
      />
      <Section
        title="Done"
        tasks={data.done}
        section="done"
        emptyMessage="Nothing marked done yet today."
        now={now}
        onComplete={onComplete}
        completingId={completingId}
        canComplete={canComplete}
      />
    </div>
  );
}
