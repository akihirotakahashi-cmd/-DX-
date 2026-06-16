"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import api, { ReviewDetail } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { useAuthStore } from "@/store/auth";
import { CheckCircle, RotateCcw, XCircle, ChevronLeft } from "lucide-react";

type Action = "approved" | "returned" | "rejected";

const ACTION_META: Record<Action, { label: string; variant: "primary" | "secondary" | "danger"; icon: React.ReactNode }> = {
  approved: { label: "承認", variant: "primary", icon: <CheckCircle className="h-4 w-4" /> },
  returned: { label: "差し戻し", variant: "secondary", icon: <RotateCcw className="h-4 w-4" /> },
  rejected: { label: "却下", variant: "danger", icon: <XCircle className="h-4 w-4" /> },
};

const STEP_ROLE: Record<number, string> = { 1: "TL", 2: "マネージャー" };
const ACTION_LABEL: Record<string, string> = {
  submitted: "提出",
  approved: "承認",
  returned: "差し戻し",
  rejected: "却下",
};

export default function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { role } = useAuthStore();
  const [detail, setDetail] = useState<ReviewDetail | null>(null);
  const [contentText, setContentText] = useState<string | null>(null);
  const [comment, setComment] = useState("");
  const [acting, setActing] = useState<Action | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ReviewDetail>(`/reviews/${id}`).then((r) => {
      setDetail(r.data);
      setLoading(false);
      if (r.data.content_url) {
        // S3 から本文を取得 (presigned URL が必要な場合は /proposals/{id}/content-url を経由)
        api.get<{ url: string }>(`/proposals/${id}/content-url`).then((urlRes) => {
          fetch(urlRes.data.url)
            .then((res) => res.text())
            .then(setContentText);
        }).catch(() => {});
      }
    });
  }, [id]);

  const isMyTurn =
    (role === "tl" && detail?.status === "reviewing_tl") ||
    (role === "manager" && detail?.status === "reviewing_mgr");

  const handleAction = async (action: Action) => {
    if (!detail) return;
    setActing(action);
    await api.post(`/reviews/${detail.id}`, { action, comment: comment || undefined });
    router.push("/reviews");
  };

  if (loading) return <p className="text-gray-400">読み込み中...</p>;
  if (!detail) return <p className="text-red-500">レビューが見つかりません</p>;

  return (
    <div className="mx-auto max-w-4xl space-y-6">
      {/* 戻るボタン */}
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ChevronLeft className="h-4 w-4" />
        レビュー一覧に戻る
      </button>

      {/* ヘッダー */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-sm text-gray-500">{detail.municipality_name}</p>
          <h1 className="mt-0.5 text-2xl font-bold">{detail.theme}</h1>
        </div>
        <StatusBadge status={detail.status} className="mt-1 flex-shrink-0" />
      </div>

      {/* 提案書本文 */}
      <Card>
        <CardHeader>
          <h2 className="font-semibold">提案書内容</h2>
        </CardHeader>
        <CardBody>
          {contentText ? (
            <div
              className="prose prose-sm max-w-none overflow-y-auto rounded bg-gray-50 p-4"
              style={{ maxHeight: 480, whiteSpace: "pre-wrap", fontFamily: "inherit" }}
            >
              {contentText}
            </div>
          ) : (
            <p className="text-sm text-gray-400">
              {detail.content_url ? "本文を読み込み中..." : "本文がありません"}
            </p>
          )}
        </CardBody>
      </Card>

      {/* 承認アクション（自分のターン時のみ表示） */}
      {isMyTurn && (
        <Card>
          <CardHeader>
            <h2 className="font-semibold">審査</h2>
          </CardHeader>
          <CardBody className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">
                コメント（任意）
              </label>
              <textarea
                rows={3}
                value={comment}
                onChange={(e) => setComment(e.target.value)}
                placeholder="差し戻し理由や承認コメントを入力..."
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div className="flex gap-3">
              {(["approved", "returned", "rejected"] as Action[]).map((action) => {
                const { label, variant, icon } = ACTION_META[action];
                return (
                  <Button
                    key={action}
                    variant={variant}
                    loading={acting === action}
                    disabled={acting !== null}
                    onClick={() => handleAction(action)}
                  >
                    {icon}
                    {label}
                  </Button>
                );
              })}
            </div>
          </CardBody>
        </Card>
      )}

      {/* 承認履歴 */}
      {detail.steps.length > 0 && (
        <Card>
          <CardHeader>
            <h2 className="font-semibold">承認履歴</h2>
          </CardHeader>
          <CardBody className="p-0">
            <ul className="divide-y divide-gray-100">
              {detail.steps.map((step) => (
                <li key={step.id} className="flex items-start gap-4 px-6 py-4">
                  <div className="flex-shrink-0 rounded-full bg-gray-100 px-2 py-0.5 text-xs font-medium text-gray-600">
                    {STEP_ROLE[step.step_number] ?? `Step ${step.step_number}`}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium">
                        {ACTION_LABEL[step.action] ?? step.action}
                      </span>
                      <span className="text-xs text-gray-400">
                        {new Date(step.executed_at).toLocaleString("ja-JP", {
                          year: "numeric",
                          month: "numeric",
                          day: "numeric",
                          hour: "2-digit",
                          minute: "2-digit",
                        })}
                      </span>
                    </div>
                    {step.comment && (
                      <p className="mt-1 text-sm text-gray-600">{step.comment}</p>
                    )}
                  </div>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
