import { DIVISION_LABELS } from "../constants";
import type { Division } from "../types";

export function DivisionSelect({ value, onChange }: {
  value: Division;
  onChange: (division: Division) => void;
}) {
  return (
    <label>
      <span>Division</span>
      <select value={value} onChange={(event) => onChange(event.target.value as Division)}>
        {(Object.keys(DIVISION_LABELS) as Division[]).map((division) => (
          <option key={division} value={division}>{DIVISION_LABELS[division]}</option>
        ))}
      </select>
    </label>
  );
}
