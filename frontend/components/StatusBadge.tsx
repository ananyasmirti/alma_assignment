import type { LeadState } from "@/lib/api";

export default function StatusBadge({ state }: { state: LeadState }) {
  const styles: Record<LeadState, string> = {
    PENDING: "bg-yellow-100 text-yellow-800",
    REACHED_OUT: "bg-green-100 text-green-800",
  };
  const labels: Record<LeadState, string> = {
    PENDING: "Pending",
    REACHED_OUT: "Reached Out",
  };
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${styles[state]}`}>
      {labels[state]}
    </span>
  );
}
