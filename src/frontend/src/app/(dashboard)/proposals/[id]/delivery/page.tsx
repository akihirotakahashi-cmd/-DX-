"use client";

import { useEffect, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import api from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { SendConfirmModal } from "@/components/delivery/SendConfirmModal";
import { ContactEmailModal } from "@/components/delivery/ContactEmailModal";
import { CheckCircle, XCircle, ExternalLink, ChevronLeft, Mail, Link2 } from "lucide-react";

interface DeliveryPrep {
  proposal_id: string;
  municipality_name: string;
  theme: string;
  approved_at: string | null;
  contact_email: string | null;
  portal_token: string | null;
  portal_url: string | null;
  sent_at: string | null;
  downloaded_at: string | null;
}

const StatusIcon = ({ ok }: { ok: boolean }) =>
  ok
    ? <CheckCircle className="h-5 w-5 text-green-500" />
    : <XCircle className="h-5 w-5 text-gray-300" />;

export default function DeliveryPrepPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const [prep, setPrep] = useState<DeliveryPrep | null>(null);
  const [loading, setLoading] = useState(true);
  const [issuing, setIssuing] = useState(false);
  const [showSend, setShowSend] = useState(false);
  const [showContactEmail, setShowContactEmail] = useState(false);
  const [copied, setCopied] = useState(false);

  const load = async () => {
    const res = await api.get<DeliveryPrep>(`/proposals/${id}/delivery`);
    setPrep(res.data);
    setLoading(false);
  };

  useEffect(() => { load(); }, [id]);

  const handleIssue = async () => {
    setIssuing(true);
    await api.post(`/proposals/${id}/portal-urls`);
    setIssuing(false);
    load();
  };

  const handleCopy = () => {
    if (!prep?.portal_url) return;
    navigator.clipboard.writeText(prep.portal_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (loading) return <p className="text-gray-400">読み込み中...</p>;
  if (!prep) return <p className="text-red-500">データが見つかりません</p>;

  const canSend = !!prep.portal_url && !!prep.contact_email && !prep.sent_at;

  return (
    <div className="mx-auto max-w-2xl space-y-6">
      <button
        onClick={() => router.back()}
        className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
      >
        <ChevronLeft className="h-4 w-4" />
        納品一覧に戻る
      </button>

      <div>
        <p className="text-sm text-gray-500">{prep.municipality_name}</p>
        <h1 className="mt-0.5 text-2xl font-bold">{prep.theme}</h1>
        {prep.approved_at && (
          <p className="mt-1 text-xs text-gray-400">
            承認日: {new Date(prep.approved_at).toLocaleDateString("ja-JP")}
          </p>
        )}
      </div>

      {/* ステップ概要 */}
      <div className="grid grid-cols-3 gap-4">
        {[
          { label: "URL発行", done: !!prep.portal_url },
          { label: "メール送信", done: !!prep.sent_at },
          { label: "ダウンロード確認", done: !!prep.downloaded_at },
        ].map(({ label, done }) => (
          <div
            key={label}
            className="flex items-center gap-2 rounded-lg border border-gray-200 bg-white px-4 py-3"
          >
            <StatusIcon ok={done} />
            <span className="text-sm font-medium text-gray-700">{label}</span>
          </div>
        ))}
      </div>

      {/* 担当者メール設定 */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <h2 className="font-semibold">送付先メールアドレス</h2>
            <Button size="sm" variant="ghost" onClick={() => setShowContactEmail(true)}>
              {prep.contact_email ? "変更" : "設定する"}
            </Button>
          </div>
        </CardHeader>
        <CardBody>
          {prep.contact_email ? (
            <div className="flex items-center gap-2 text-sm">
              <Mail className="h-4 w-4 text-gray-400" />
              <span>{prep.contact_email}</span>
            </div>
          ) : (
            <p className="text-sm text-amber-600">
              担当者メールアドレスが未設定です。メール送信前に設定してください。
            </p>
          )}
        </CardBody>
      </Card>

      {/* Step 1: URL 発行 */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-primary-600 text-xs font-bold text-white">
              1
            </div>
            <h2 className="font-semibold">ポータル URL 発行</h2>
          </div>
        </CardHeader>
        <CardBody className="space-y-3">
          {prep.portal_url ? (
            <>
              <div className="flex items-center gap-2 rounded-md border border-gray-200 bg-gray-50 px-3 py-2">
                <Link2 className="h-4 w-4 flex-shrink-0 text-gray-400" />
                <span className="flex-1 truncate text-sm font-mono text-gray-700">{prep.portal_url}</span>
                <button
                  onClick={handleCopy}
                  className="flex-shrink-0 text-xs text-primary-600 hover:underline"
                >
                  {copied ? "コピー済み" : "コピー"}
                </button>
              </div>
              <a
                href={prep.portal_url}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-sm text-primary-600 hover:underline"
              >
                ポータルを確認 <ExternalLink className="h-3.5 w-3.5" />
              </a>
            </>
          ) : (
            <Button loading={issuing} onClick={handleIssue}>
              URL を発行する
            </Button>
          )}
        </CardBody>
      </Card>

      {/* Step 2: メール送信 */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white ${
                prep.portal_url ? "bg-primary-600" : "bg-gray-300"
              }`}
            >
              2
            </div>
            <h2 className="font-semibold">自治体へのメール送信</h2>
          </div>
        </CardHeader>
        <CardBody>
          {prep.sent_at ? (
            <div className="flex items-center gap-2 text-sm text-green-700">
              <CheckCircle className="h-4 w-4" />
              {new Date(prep.sent_at).toLocaleString("ja-JP", {
                year: "numeric",
                month: "numeric",
                day: "numeric",
                hour: "2-digit",
                minute: "2-digit",
              })} に送信済み
            </div>
          ) : (
            <Button
              disabled={!canSend}
              onClick={() => setShowSend(true)}
              title={
                !prep.portal_url
                  ? "先にURL発行してください"
                  : !prep.contact_email
                  ? "先に担当者メールを設定してください"
                  : undefined
              }
            >
              メールを送信する
            </Button>
          )}
          {!prep.portal_url && (
            <p className="mt-2 text-xs text-gray-400">Step 1 が完了してから送信できます</p>
          )}
        </CardBody>
      </Card>

      {/* Step 3: ダウンロード確認 */}
      <Card>
        <CardHeader>
          <div className="flex items-center gap-3">
            <div
              className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold text-white ${
                prep.sent_at ? "bg-primary-600" : "bg-gray-300"
              }`}
            >
              3
            </div>
            <h2 className="font-semibold">ダウンロード確認</h2>
          </div>
        </CardHeader>
        <CardBody>
          {prep.downloaded_at ? (
            <div className="flex items-center gap-2 text-sm text-green-700">
              <CheckCircle className="h-4 w-4" />
              {new Date(prep.downloaded_at).toLocaleString("ja-JP", {
                year: "numeric", month: "numeric", day: "numeric",
                hour: "2-digit", minute: "2-digit",
              })} にダウンロード済み
            </div>
          ) : (
            <p className="text-sm text-gray-500">
              自治体担当者がポータルでダウンロードすると自動で記録されます。
            </p>
          )}
        </CardBody>
      </Card>

      {/* モーダル */}
      {showSend && prep.contact_email && (
        <SendConfirmModal
          proposalId={id}
          municipalityName={prep.municipality_name}
          contactEmail={prep.contact_email}
          onClose={() => setShowSend(false)}
          onSent={() => { setShowSend(false); load(); }}
        />
      )}
      {showContactEmail && (
        <ContactEmailModal
          tenantId={prep.proposal_id}
          currentEmail={prep.contact_email}
          onClose={() => setShowContactEmail(false)}
          onSaved={() => { setShowContactEmail(false); load(); }}
        />
      )}
    </div>
  );
}
