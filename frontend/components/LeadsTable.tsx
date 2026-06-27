"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import type { Lead } from "@/lib/api";
import { updateLeadState } from "@/lib/api";
import StatusBadge from "./StatusBadge";

interface Props {
  leads: Lead[];
  token: string;
}

export default function LeadsTable({ leads, token }: Props) {
  const router = useRouter();
  const [loading, setLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function handleDownloadResume(leadId: string) {
    try {
      const res = await fetch(`/api/v1/leads/${leadId}/resume`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Failed to fetch resume");

      const contentDisposition = res.headers.get("content-disposition") ?? "";
      const fileNameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/);
      const fileName = fileNameMatch?.[1] ?? `resume-${leadId}`;

      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = fileName;
      anchor.click();
      URL.revokeObjectURL(url);
    } catch {
      setError("Failed to download resume. Please try again.");
    }
  }

  async function handleMarkReachedOut(leadId: string) {
    setLoading(leadId);
    setError(null);
    try {
      await updateLeadState(token, leadId);
      router.refresh();
    } catch {
      setError("Failed to update lead status. Please try again.");
    } finally {
      setLoading(null);
    }
  }

  if (leads.length === 0) {
    return (
      <div className="bg-white rounded-xl border border-gray-200 p-12 text-center">
        <p className="text-gray-400 text-sm">No leads found</p>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-700">
          {error}
        </div>
      )}

      <div className="bg-white rounded-xl border border-gray-200 overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Email
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Submitted
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Resume
              </th>
              <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Action
              </th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {leads.map((lead) => (
              <tr key={lead.id} className="hover:bg-gray-50 transition-colors">
                <td className="px-6 py-4 whitespace-nowrap">
                  <span className="text-sm font-medium text-gray-900">
                    {lead.first_name} {lead.last_name}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <a
                    href={`mailto:${lead.email}`}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    {lead.email}
                  </a>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <StatusBadge state={lead.state} />
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {new Date(lead.created_at).toLocaleDateString("en-US", {
                    year: "numeric",
                    month: "short",
                    day: "numeric",
                  })}
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                  <button
                    onClick={() => handleDownloadResume(lead.id)}
                    className="text-sm text-blue-600 hover:underline"
                  >
                    Download
                  </button>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right">
                  {lead.state === "PENDING" ? (
                    <button
                      onClick={() => handleMarkReachedOut(lead.id)}
                      disabled={loading === lead.id}
                      className="text-sm bg-green-600 text-white px-3 py-1.5 rounded-lg hover:bg-green-700 disabled:opacity-50 transition-colors"
                    >
                      {loading === lead.id ? "Updating..." : "Mark as Reached Out"}
                    </button>
                  ) : (
                    <span className="text-xs text-gray-400 italic">Done</span>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
