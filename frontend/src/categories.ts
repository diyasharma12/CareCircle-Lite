import type { TaskCategory } from "./types";

export const CATEGORY_META: Record<TaskCategory, { label: string; icon: string }> = {
  medicine: { label: "Medicine", icon: "💊" },
  appointment: { label: "Appointment", icon: "🩺" },
  checkin: { label: "Check-in call", icon: "📞" },
  other: { label: "Other", icon: "📝" },
};
