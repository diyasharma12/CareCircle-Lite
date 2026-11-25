import type { FamilyMember } from "../types";

interface Props {
  members: FamilyMember[];
  selectedId: string | null;
  onChange: (id: string) => void;
}

export default function WhoAmI({ members, selectedId, onChange }: Props) {
  return (
    <div className="whoami">
      <label htmlFor="whoami-select">I am</label>
      <select
        id="whoami-select"
        value={selectedId ?? ""}
        onChange={(e) => onChange(e.target.value)}
      >
        <option value="" disabled>
          Choose your name
        </option>
        {members.map((m) => (
          <option key={m.id} value={m.id}>
            {m.name}
            {m.relation ? ` (${m.relation})` : ""}
          </option>
        ))}
      </select>
    </div>
  );
}
