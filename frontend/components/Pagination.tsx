import type { LeadState } from "@/lib/api";
import Link from "next/link";

interface Props {
  currentPage: number;
  totalPages: number;
  state?: LeadState;
}

function buildHref(page: number, state?: LeadState): string {
  const params = new URLSearchParams({ page: String(page) });
  if (state) params.set("state", state);
  return `/dashboard?${params}`;
}

export default function Pagination({ currentPage, totalPages, state }: Props) {
  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);

  return (
    <div className="flex items-center justify-center gap-1">
      <Link
        href={buildHref(currentPage - 1, state)}
        aria-disabled={currentPage === 1}
        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
          currentPage === 1
            ? "text-gray-300 cursor-not-allowed pointer-events-none"
            : "text-gray-600 hover:bg-gray-100"
        }`}
      >
        ← Prev
      </Link>

      {pages.map((p) => (
        <Link
          key={p}
          href={buildHref(p, state)}
          className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
            p === currentPage
              ? "bg-blue-600 text-white"
              : "text-gray-600 hover:bg-gray-100"
          }`}
        >
          {p}
        </Link>
      ))}

      <Link
        href={buildHref(currentPage + 1, state)}
        aria-disabled={currentPage === totalPages}
        className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
          currentPage === totalPages
            ? "text-gray-300 cursor-not-allowed pointer-events-none"
            : "text-gray-600 hover:bg-gray-100"
        }`}
      >
        Next →
      </Link>
    </div>
  );
}
