import { getServerSession } from "next-auth";
import { authOptions } from "@/lib/auth";
import { listLeads, type LeadState } from "@/lib/api";
import LeadsTable from "@/components/LeadsTable";
import Pagination from "@/components/Pagination";

interface PageProps {
  searchParams: { page?: string; state?: string };
}

export default async function DashboardPage({ searchParams }: PageProps) {
  const session = await getServerSession(authOptions);
  const token = (session as any)?.accessToken as string;

  const page = Number(searchParams.page ?? 1);
  const state = searchParams.state as LeadState | undefined;

  const data = await listLeads(token, page, 20, state);

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
        <h1 className="text-xl font-semibold text-gray-900">Lead Dashboard</h1>
        <form method="POST" action="/api/auth/signout">
          <button
            type="submit"
            className="text-sm text-gray-500 hover:text-gray-900 transition-colors"
          >
            Sign out
          </button>
        </form>
      </header>

      <main className="max-w-7xl mx-auto px-6 py-8 space-y-6">
        {/* Filters */}
        <div className="flex gap-3 items-center">
          <span className="text-sm text-gray-500">Filter by status:</span>
          <a
            href="/dashboard"
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              !state
                ? "bg-blue-100 text-blue-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            All
          </a>
          <a
            href="/dashboard?state=PENDING"
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              state === "PENDING"
                ? "bg-yellow-100 text-yellow-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Pending
          </a>
          <a
            href="/dashboard?state=REACHED_OUT"
            className={`px-3 py-1 rounded-full text-sm font-medium transition-colors ${
              state === "REACHED_OUT"
                ? "bg-green-100 text-green-700"
                : "bg-gray-100 text-gray-600 hover:bg-gray-200"
            }`}
          >
            Reached Out
          </a>
        </div>

        {/* Stats */}
        <p className="text-sm text-gray-500">
          {data.total} lead{data.total !== 1 ? "s" : ""} found
        </p>

        <LeadsTable leads={data.items} token={token} />

        {data.total_pages > 1 && (
          <Pagination
            currentPage={data.page}
            totalPages={data.total_pages}
            state={state}
          />
        )}
      </main>
    </div>
  );
}
