import api from "./client";

export interface ReceiptItemPayload {
  id?: string;
  name: string;
  brand?: string;
  quantity?: number | string;
  unit?: string;
  unit_price?: number | string | null;
  total_price?: number | string | null;
  tags?: string[];
  confidence?: number | string | null;
  line_index?: number;
  main_category?: string;
  sub_category?: string;
  target_org_id?: string | null;
}

export interface ReceiptPayload {
  merchant?: string;
  address?: string;
  purchased_at?: string | null;
  currency?: string;
  subtotal?: number | string | null;
  tax?: number | string | null;
  discount?: number | string | null;
  total?: number | string | null;
  notes?: string;
  payer?: string;
  items?: ReceiptItemPayload[];
}

export async function fetchStats(startDate?: string, endDate?: string) {
  const params = new URLSearchParams();
  if (startDate) params.set("start_date", startDate);
  if (endDate) params.set("end_date", endDate);
  const qs = params.toString();
  const { data } = await api.get(`/stats/overview/${qs ? `?${qs}` : ""}`);
  return data;
}

export async function listReceipts() {
  const { data } = await api.get("/receipts/");
  return data;
}

export async function getReceipt(id: string) {
  const { data } = await api.get(`/receipts/${id}/`);
  return data;
}

export async function createReceipt(payload?: ReceiptPayload) {
  const { data } = await api.post("/receipts/", payload || {});
  return data;
}

export async function uploadReceipt(file: File, payer?: string) {
  const form = new FormData();
  form.append("image", file);
  if (payer) form.append("payer", payer);
  const { data } = await api.post("/receipts/", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 360000
  });
  if (data.status === "failed") {
    throw new Error(data.raw_model_output || "AI 模型解析失败");
  }
  return data;
}

export async function uploadReceiptStream(
  file: File,
  payer: string,
  onPhase: (phase: string) => void,
): Promise<any> {
  const baseURL = import.meta.env.VITE_API_BASE || `${import.meta.env.BASE_URL}api`;
  const token = localStorage.getItem("access_token");
  const orgId = localStorage.getItem("active_org_id");

  const form = new FormData();
  form.append("image", file);
  if (payer) form.append("payer", payer);

  const headers: Record<string, string> = {};
  if (token) headers["Authorization"] = `Bearer ${token}`;
  if (orgId) headers["X-Active-Org"] = orgId;

  const res = await fetch(`${baseURL}/receipts/upload-stream/`, {
    method: "POST",
    headers,
    body: form,
  });

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "请求失败" }));
    throw new Error(err.detail || "请求失败");
  }

  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let result: any = null;

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const lines = buffer.split("\n");
    buffer = lines.pop() || "";

    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const data = JSON.parse(line.slice(6));

      if (data.phase === "thinking" || data.phase === "generating") {
        onPhase(data.phase);
      } else if (data.phase === "error") {
        throw new Error(data.detail || "解析失败");
      } else if (data.phase === "done") {
        result = data.receipt;
      }
    }
  }

  if (!result) throw new Error("未收到解析结果");
  if (result.status === "failed") {
    throw new Error(result.raw_model_output || "AI 模型解析失败");
  }
  return result;
}

export async function updateReceipt(id: string, payload: ReceiptPayload) {
  const { data } = await api.put(`/receipts/${id}/`, payload);
  return data;
}

export async function confirmReceipt(id: string) {
  const { data } = await api.post(`/receipts/${id}/confirm/`);
  return data;
}

export async function confirmReceiptWithSplit(
  id: string,
  itemOrgs: Record<string, string>,
) {
  const { data } = await api.post(`/receipts/${id}/confirm/`, { item_orgs: itemOrgs });
  return data;
}

export async function moveReceiptItems(
  id: string,
  moves: Array<{ item_id: string | number; target_org_id: string }>,
) {
  const { data } = await api.post(`/receipts/${id}/move-items/`, { moves });
  return data;
}

export async function deleteReceipt(id: string) {
  await api.delete(`/receipts/${id}/`);
}
