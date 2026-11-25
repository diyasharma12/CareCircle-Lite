export type TaskCategory = "medicine" | "appointment" | "checkin" | "other";
export type TaskStatus = "pending" | "done";

export interface FamilyMember {
  id: string;
  name: string;
  relation: string | null;
}

export interface CareRecipient {
  id: string;
  name: string;
  notes: string | null;
}

export interface CareTask {
  id: string;
  recipient_id: string;
  title: string;
  category: TaskCategory;
  due_at: string;
  status: TaskStatus;
  notes: string | null;
  created_by: FamilyMember | null;
  completed_by: FamilyMember | null;
  completed_at: string | null;
  created_at: string;
}

export interface TodayResponse {
  overdue: CareTask[];
  due: CareTask[];
  done: CareTask[];
  as_of: string;
}
