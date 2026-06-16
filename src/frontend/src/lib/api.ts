import axios from "axios";
import { useAuthStore } from "@/store/auth";
import { toast } from "@/store/toast";

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1",
  headers: { "Content-Type": "application/json" },
});

api.interceptors.request.use((config) => {
  const token = useAuthStore.getState().idToken;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

const ERROR_MESSAGES: Record<number, string> = {
  400: "リクエストの内容が不正です",
  401: "セッションが切れました。再ログインしてください",
  403: "この操作を行う権限がありません",
  404: "リソースが見つかりません",
  409: "操作が競合しました。状態を確認してください",
  422: "入力内容を確認してください",
  500: "サーバーエラーが発生しました。しばらくお待ちください",
};

api.interceptors.response.use(
  (res) => res,
  (err) => {
    const status: number | undefined = err.response?.status;
    if (status === 401) {
      useAuthStore.getState().signOut();
      window.location.href = "/login";
      return Promise.reject(err);
    }
    // 204 は body なし — エラー扱いしない
    if (status && status !== 204) {
      const serverMsg = err.response?.data?.detail;
      const msg =
        typeof serverMsg === "string"
          ? serverMsg
          : ERROR_MESSAGES[status] ?? `エラーが発生しました (${status})`;
      toast.error(msg);
    }
    return Promise.reject(err);
  }
);

export default api;

// --- typed helpers -----------------------------------------------------------

export type ProposalRead = Proposal;

export interface Proposal {
  id: string;
  tenant_id: string;
  municipality_name: string;
  theme: string;
  status: string;
  content_text: string | null;
  // 入力フィールド
  future_vision: string | null;
  current_state: string | null;
  challenges: string | null;
  root_causes: string | null;
  reference_urls: string[];
  attachment_names: string[];
  refine_instruction: string | null;
  parent_proposal_id: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProposalDetail extends Proposal {
  content_url: string | null;
  parent_proposal_id: string | null;
  approved_at: string | null;
  evidence: Evidence[];
}

export interface Evidence {
  id: string;
  source_name: string;
  source_url: string | null;
  excerpt: string | null;
  classification: string;
}

export interface ReviewItem {
  id: string;
  municipality_name: string;
  theme: string;
  status: string;
  created_at: string;
}

export interface Notification {
  id: string;
  type: string;
  message: string;
  link_url: string | null;
  read: boolean;
  created_at: string;
}

export interface ApprovalStep {
  id: string;
  step_number: number;
  action: string;
  comment: string | null;
  executed_at: string;
}

export interface ReviewDetail {
  id: string;
  municipality_name: string;
  theme: string;
  status: string;
  created_at: string;
  content_url: string | null;
  parent_proposal_id: string | null;
  steps: ApprovalStep[];
}

export interface DeliveryItem {
  id: string;
  municipality_name: string;
  theme: string;
  approved_at: string | null;
  portal_issued: boolean;
  portal_sent: boolean;
}
