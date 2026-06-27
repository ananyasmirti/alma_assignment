const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type LeadState = "PENDING" | "REACHED_OUT";

export interface Lead {
  id: string;
  first_name: string;
  last_name: string;
  email: string;
  state: LeadState;
  resume_path: string;
  created_at: string;
  updated_at: string;
}

export interface PaginatedLeads {
  items: Lead[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

export async function createLead(formData: FormData): Promise<Lead> {
  const res = await fetch(`${API_URL}/api/v1/leads`, {
    method: "POST",
    body: formData,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Unknown error" }));
    throw new Error(err.detail ?? "Failed to submit application");
  }
  return res.json();
}

export async function listLeads(
  token: string,
  page = 1,
  pageSize = 20,
  state?: LeadState
): Promise<PaginatedLeads> {
  const params = new URLSearchParams({
    page: String(page),
    page_size: String(pageSize),
  });
  if (state) params.set("state", state);

  const res = await fetch(`${API_URL}/api/v1/leads?${params}`, {
    headers: { Authorization: `Bearer ${token}` },
    cache: "no-store",
  });
  if (!res.ok) throw new Error("Failed to fetch leads");
  return res.json();
}

export async function updateLeadState(
  token: string,
  leadId: string
): Promise<Lead> {
  const res = await fetch(`${API_URL}/api/v1/leads/${leadId}/state`, {
    method: "PATCH",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ state: "REACHED_OUT" }),
  });
  if (!res.ok) throw new Error("Failed to update lead state");
  return res.json();
}

export function resumeUrl(leadId: string, token: string): string {
  return `${API_URL}/api/v1/leads/${leadId}/resume?token=${encodeURIComponent(token)}`;
}
