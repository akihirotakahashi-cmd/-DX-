"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import { AlertTriangle, ArrowLeft, Save, Send } from "lucide-react";
import api from "@/lib/api";
import { toast } from "@/store/toast";
import { Button } from "@/components/ui/Button";

export default function EditProposalPage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const [content, setContent]     = useState("");
  const [original, setOriginal]   = useState("");
  const [loading, setLoading]     = useState(true);
  const [saving, setSaving]       = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const isDirty = content !== original;

  // 本文を取得
  useEffect(() => {
    api.get<{ content_text: string }>(`/proposals/${id}/text`).then((r) => {
      setContent(r.data.content_text ?? "");
      setOriginal(r.data.content_text ?? "");
    }).finally(() => setLoading(false));
  }, [id]);

  // ブラウザの「ページを離れる前に確認」
  useEffect(() => {
    const handler = (e: BeforeUnloadEvent) => {
      if (isDirty) { e.preventDefault(); e.returnValue = ""; }
    };
    window.addEventListener("beforeunload", handler);
    return () => window.removeEventListener("beforeunload", handler);
  }, [isDirty]);

  const handleSave = async () => {
    setSaving(true);
    try {
      await api.put(`/proposals/${id}/content`, { content_text: content });
      setOriginal(content);
      toast.success("保存しました");
    } finally {
      setSaving(false);
    }
  };

  const handleSubmit = async () => {
    if (isDirty) await handleSave();
    setSubmitting(true);
    try {
      await api.post(`/proposals/${id}/submit`);
      toast.success("TL レビューに提出しました");
      router.push("/proposals");
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    // Cmd+S / Ctrl+S で保存
    if ((e.metaKey || e.ctrlKey) && e.key === "s") {
      e.preventDefault();
      handleSave();
    }
    // Tab でインデント挿入
    if (e.key === "Tab") {
      e.preventDefault();
      const el = textareaRef.current!;
      const start = el.selectionStart;
      const end = el.selectionEnd;
      const next = content.substring(0, start) + "  " + content.substring(end);
      setContent(next);
      requestAnimationFrame(() => {
        el.selectionStart = el.selectionEnd = start + 2;
      });
    }
  };

  if (loading) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary-500 border-t-transparent" />
      </div>
    );
  }

  return (
    // -m-6 で親の p-6 パディングを相殺、h 計算に合わせて全画面化
    <div className="-m-6 flex flex-col" style={{ height: "calc(100vh - 4rem)" }}>
      {/* ── ヘッダーバー ── */}
      <div className="flex shrink-0 items-center justify-between border-b border-gray-200 bg-white px-4 py-2.5">
        <div className="flex items-center gap-3">
          <button
            onClick={() => {
              if (isDirty && !confirm("未保存の変更があります。ページを離れますか？")) return;
              router.push("/proposals");
            }}
            className="flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700"
          >
            <ArrowLeft className="h-4 w-4" />
            一覧に戻る
          </button>

          {isDirty && (
            <span className="flex items-center gap-1 text-xs text-amber-600">
              <AlertTriangle className="h-3.5 w-3.5" />
              未保存の変更があります
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          <span className="hidden text-xs text-gray-400 sm:block">⌘S で保存</span>
          <Button
            variant="secondary"
            size="sm"
            onClick={handleSave}
            disabled={saving || !isDirty}
          >
            <Save className="mr-1 h-3.5 w-3.5" />
            {saving ? "保存中..." : "保存"}
          </Button>
          <Button
            size="sm"
            onClick={handleSubmit}
            disabled={submitting}
          >
            <Send className="mr-1 h-3.5 w-3.5" />
            {submitting ? "提出中..." : "TL に提出"}
          </Button>
        </div>
      </div>

      {/* ── エディタ本体 ── */}
      <div className="flex min-h-0 flex-1 gap-0">
        {/* 左ペイン: エディタ */}
        <div className="flex min-h-0 flex-1 flex-col border-r border-gray-200">
          <div className="shrink-0 border-b border-gray-100 bg-gray-50 px-4 py-1.5 text-xs font-medium text-gray-500">
            Markdown
          </div>
          <textarea
            ref={textareaRef}
            value={content}
            onChange={(e) => setContent(e.target.value)}
            onKeyDown={handleKeyDown}
            spellCheck={false}
            className="flex-1 resize-none bg-white px-6 py-4 font-mono text-sm leading-relaxed text-gray-800 focus:outline-none"
            placeholder="提案書の内容を入力してください..."
          />
        </div>

        {/* 右ペイン: プレビュー */}
        <div className="flex min-h-0 flex-1 flex-col">
          <div className="shrink-0 border-b border-gray-100 bg-gray-50 px-4 py-1.5 text-xs font-medium text-gray-500">
            プレビュー
          </div>
          <div
            className="prose prose-sm max-w-none flex-1 overflow-y-auto px-6 py-4"
            style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}
          >
            {content || <span className="text-gray-300">プレビューがここに表示されます</span>}
          </div>
        </div>
      </div>
    </div>
  );
}
