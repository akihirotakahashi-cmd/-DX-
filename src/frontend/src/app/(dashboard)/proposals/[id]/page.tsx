"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  ChevronDown, ChevronRight, Send, Plus, SkipForward,
  Paperclip, Link2, ArrowLeft,
} from "lucide-react";
import api, { Proposal } from "@/lib/api";
import { useAuthStore } from "@/store/auth";
import { toast } from "@/store/toast";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";

// ── クイック指示ボタン定義
const QUICK_ACTIONS = [
  { label: "もっと具体的に",     value: "各施策をもっと具体的に詳しく説明してください。実装手順・技術仕様を含めてください。" },
  { label: "別案を出して",        value: "全く異なるアプローチで、別の施策を提案してください。" },
  { label: "コスト・予算詳細",    value: "各施策のコスト・予算についてより詳しく説明し、費用対効果を示してください。" },
  { label: "スケジュール詳細",    value: "実施スケジュールとロードマップをフェーズ別により詳しく説明してください。" },
  { label: "導入事例を追加",      value: "他の自治体での導入事例や実績データを追加してください。" },
  { label: "リスクと対策を追加",  value: "各施策のリスクと対策を詳しく追加してください。" },
];

interface Measure {
  index: number;
  title: string;
}

type Phase = "loading" | "idle" | "streaming" | "selecting" | "deepening";

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/** SSE ストリームを読む */
async function readSse(
  res: Response,
  onChunk: (t: string) => void,
  onMeasures: (m: Measure[]) => void,
  onDone: (id: string) => void,
) {
  const reader = res.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  let pendingEvent = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";

    for (const line of lines) {
      if (line.startsWith("event: ")) { pendingEvent = line.slice(7).trim(); continue; }
      if (line === "") { pendingEvent = ""; continue; }
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6);

      if (pendingEvent === "measures") {
        try { onMeasures(JSON.parse(payload)); } catch {}
        pendingEvent = "";
        continue;
      }
      if (pendingEvent === "done" || /^[0-9a-f-]{36}$/.test(payload.trim())) {
        onDone(payload.trim());
        continue;
      }
      onChunk(payload.replace(/<br>/g, "\n"));
    }
  }
}

// ── 元の入力内容アコーディオン
function InputSummary({ proposal }: { proposal: Proposal }) {
  const [open, setOpen] = useState(false);
  return (
    <div className="rounded-xl border border-gray-200 bg-gray-50">
      <button
        className="flex w-full items-center gap-2 px-5 py-3 text-left text-sm font-medium text-gray-600 hover:bg-gray-100 transition-colors rounded-xl"
        onClick={() => setOpen((o) => !o)}
      >
        {open ? <ChevronDown className="h-4 w-4" /> : <ChevronRight className="h-4 w-4" />}
        元の入力内容を確認する
      </button>
      {open && (
        <div className="border-t border-gray-200 px-5 py-4 space-y-3 text-sm">
          {[
            { label: "実現したい将来像", value: proposal.future_vision },
            { label: "現在像",           value: proposal.current_state },
            { label: "抱えている課題",   value: proposal.challenges },
            { label: "課題の原因",       value: proposal.root_causes },
          ].map(({ label, value }) => (
            value ? (
              <div key={label}>
                <p className="font-medium text-gray-500">{label}</p>
                <p className="mt-0.5 whitespace-pre-wrap text-gray-700">{value}</p>
              </div>
            ) : null
          ))}
          {proposal.attachment_names.length > 0 && (
            <div>
              <p className="font-medium text-gray-500 flex items-center gap-1">
                <Paperclip className="h-3.5 w-3.5" /> 添付ファイル
              </p>
              <ul className="mt-0.5 space-y-0.5">
                {proposal.attachment_names.map((n) => (
                  <li key={n} className="text-gray-700">{n}</li>
                ))}
              </ul>
            </div>
          )}
          {proposal.reference_urls.length > 0 && (
            <div>
              <p className="font-medium text-gray-500 flex items-center gap-1">
                <Link2 className="h-3.5 w-3.5" /> 参照URL
              </p>
              <ul className="mt-0.5 space-y-0.5">
                {proposal.reference_urls.map((u) => (
                  <li key={u} className="break-all text-primary-600">{u}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

// ── 提案書バージョン表示
function ProposalVersion({
  proposal,
  versionNum,
  isLatest,
}: {
  proposal: Proposal;
  versionNum: number;
  isLatest: boolean;
}) {
  const [open, setOpen] = useState(isLatest);
  return (
    <div className="rounded-xl border border-gray-200 bg-white shadow-sm">
      <button
        className="flex w-full items-center justify-between gap-4 px-5 py-3 text-left hover:bg-gray-50 transition-colors"
        onClick={() => setOpen((o) => !o)}
      >
        <div className="flex items-center gap-2">
          {open ? <ChevronDown className="h-4 w-4 text-gray-400" /> : <ChevronRight className="h-4 w-4 text-gray-400" />}
          <span className="font-medium text-gray-700">
            v{versionNum}
            {isLatest && (
              <span className="ml-2 rounded bg-primary-100 px-1.5 py-0.5 text-xs font-medium text-primary-700">
                最新
              </span>
            )}
          </span>
          <span className="text-xs text-gray-400">
            {new Date(proposal.created_at).toLocaleString("ja-JP", {
              month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit",
            })}
          </span>
        </div>
        <StatusBadge status={proposal.status} />
      </button>
      {open && (
        <div className="border-t border-gray-100">
          <div
            className="prose prose-sm max-w-none px-5 py-4"
            style={{ whiteSpace: "pre-wrap", fontFamily: "inherit" }}
          >
            {proposal.content_text || <span className="text-gray-400">本文が未生成です</span>}
          </div>
        </div>
      )}
    </div>
  );
}

// ── 施策選択パネル
function MeasureSelector({
  measures,
  selected,
  onToggle,
  onDeepen,
  onSkip,
  loading,
}: {
  measures: Measure[];
  selected: Set<number>;
  onToggle: (idx: number) => void;
  onDeepen: () => void;
  onSkip: () => void;
  loading: boolean;
}) {
  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold text-gray-800">採用する施策を選択してください</h3>
        <p className="mt-0.5 text-sm text-gray-500">
          チェックした施策について詳細計画（定量分析・ロードマップ・出典）を生成します
        </p>
      </CardHeader>
      <CardBody className="space-y-2">
        {measures.map((m) => (
          <label
            key={m.index}
            className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${
              selected.has(m.index)
                ? "border-primary-400 bg-primary-50"
                : "border-gray-200 hover:border-gray-300"
            }`}
          >
            <input
              type="checkbox"
              checked={selected.has(m.index)}
              onChange={() => onToggle(m.index)}
              className="h-4 w-4 rounded border-gray-300 text-primary-600 focus:ring-primary-500"
            />
            <span className="text-sm font-medium text-gray-700">
              {"①②③④⑤⑥⑦⑧⑨⑩"[m.index - 1]} {m.title}
            </span>
            {selected.has(m.index) && (
              <span className="ml-auto text-xs font-medium text-primary-600">採用する ✓</span>
            )}
          </label>
        ))}
        <div className="mt-4 flex justify-end gap-3">
          <Button variant="secondary" onClick={onSkip} disabled={loading}>
            <SkipForward className="mr-1 h-3.5 w-3.5" />
            スキップして提出へ
          </Button>
          <Button onClick={onDeepen} disabled={selected.size === 0 || loading}>
            {loading ? "生成中..." : `選択した施策を深掘り（${selected.size}件）`}
          </Button>
        </div>
      </CardBody>
    </Card>
  );
}

// ── 指示入力パネル
function InstructionPanel({
  latestId,
  onSend,
  disabled,
}: {
  latestId: string;
  onSend: (instruction: string) => void;
  disabled: boolean;
}) {
  const [custom, setCustom] = useState("");

  return (
    <Card>
      <CardHeader>
        <h3 className="font-semibold text-gray-800">次の指示を出す</h3>
        <p className="mt-0.5 text-sm text-gray-500">
          AIに追加指示を送ることで、提案書がブラッシュアップされます
        </p>
      </CardHeader>
      <CardBody className="space-y-4">
        {/* クイックボタン */}
        <div className="flex flex-wrap gap-2">
          {QUICK_ACTIONS.map((a) => (
            <button
              key={a.label}
              onClick={() => !disabled && onSend(a.value)}
              disabled={disabled}
              className="rounded-full border border-gray-300 bg-white px-3 py-1.5 text-sm text-gray-700 hover:border-primary-400 hover:text-primary-700 transition-colors disabled:opacity-40"
            >
              {a.label}
            </button>
          ))}
        </div>

        {/* カスタム指示 */}
        <div>
          <label className="mb-1 block text-sm font-medium text-gray-600">その他（自由入力）</label>
          <div className="flex gap-2">
            <textarea
              rows={2}
              value={custom}
              onChange={(e) => setCustom(e.target.value)}
              disabled={disabled}
              placeholder="例: ②の施策についてコスト削減案を追加して"
              className="flex-1 resize-none rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500 disabled:bg-gray-50"
            />
            <Button
              onClick={() => { if (custom.trim()) { onSend(custom.trim()); setCustom(""); } }}
              disabled={disabled || !custom.trim()}
              className="shrink-0 self-end"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
      </CardBody>
    </Card>
  );
}

// ──────────────────────────────────────────────
// メインページ
// ──────────────────────────────────────────────
export default function ProposalWorkspacePage() {
  const { id } = useParams<{ id: string }>();
  const router = useRouter();
  const { idToken } = useAuthStore();

  const [chain, setChain] = useState<Proposal[]>([]);
  const [phase, setPhase] = useState<Phase>("loading");
  const [streamText, setStreamText] = useState("");
  const [measures, setMeasures] = useState<Measure[]>([]);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [deepText, setDeepText] = useState("");
  const [newId, setNewId] = useState<string | null>(null);

  const streamRef = useRef<HTMLDivElement>(null);
  const deepRef   = useRef<HTMLDivElement>(null);

  const scrollBottom = (ref: React.RefObject<HTMLDivElement>) =>
    setTimeout(() => ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" }), 10);

  useEffect(() => {
    api
      .get<Proposal[]>(`/proposals/${id}/chain`)
      .then((r) => { setChain(r.data); setPhase("idle"); })
      .catch(() => { toast.error("提案書の読み込みに失敗しました"); setPhase("idle"); });
  }, [id]);

  const latest = chain[chain.length - 1];
  const root   = chain[0];
  const isDraft = latest?.status === "draft" || latest?.status === "rejected";

  const handleSubmit = async () => {
    if (!latest) return;
    await api.post(`/proposals/${latest.id}/submit`);
    toast.success("TL レビューに提出しました");
    router.push("/proposals");
  };

  // ── 精緻化指示送信
  const handleInstruction = async (instruction: string) => {
    if (!latest || phase !== "idle") return;
    setPhase("streaming");
    setStreamText("");
    setMeasures([]);
    setSelected(new Set());
    setDeepText("");
    setNewId(null);

    try {
      const res = await fetch(`${API}/proposals/${latest.id}/refine`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${idToken}` },
        body: JSON.stringify({ instruction }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      let capturedNewId = "";
      await readSse(
        res,
        (t) => { setStreamText((p) => p + t); scrollBottom(streamRef); },
        (m) => { setMeasures(m); },
        (id) => { capturedNewId = id; setNewId(id); },
      );

      if (measures.length === 0) {
        // 施策選択不要 → URL 移動（新バージョンのチェーンを表示）
        if (capturedNewId) router.push(`/proposals/${capturedNewId}`);
      } else {
        setPhase("selecting");
      }
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "生成に失敗しました");
      setPhase("idle");
    }
  };

  // ── 深掘り
  const handleDeepen = async () => {
    if (!newId || selected.size === 0) return;
    setPhase("deepening");
    setDeepText("");

    try {
      const res = await fetch(`${API}/proposals/${newId}/deepen`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${idToken}` },
        body: JSON.stringify({
          selected_measures: measures
            .filter((m) => selected.has(m.index))
            .map((m) => ({ index: m.index, title: m.title })),
          future_vision: latest?.future_vision || latest?.theme || "",
        }),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      await readSse(
        res,
        (t) => { setDeepText((p) => p + t); scrollBottom(deepRef); },
        () => {},
        () => { if (newId) router.push(`/proposals/${newId}`); },
      );
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "深掘りに失敗しました");
      setPhase("selecting");
    }
  };

  const toggleMeasure = (idx: number) =>
    setSelected((s) => { const n = new Set(s); n.has(idx) ? n.delete(idx) : n.add(idx); return n; });

  // ──────────────────────────────
  if (phase === "loading") {
    return (
      <div className="mx-auto max-w-3xl space-y-4">
        <div className="h-8 w-64 animate-pulse rounded bg-gray-200" />
        <div className="h-40 animate-pulse rounded-xl bg-gray-100" />
        <div className="h-40 animate-pulse rounded-xl bg-gray-100" />
      </div>
    );
  }

  return (
    <div className="mx-auto max-w-3xl space-y-4 pb-16">
      {/* ヘッダー */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex items-start gap-3">
          <button
            onClick={() => router.push("/proposals")}
            className="mt-1 text-gray-400 hover:text-gray-600 transition-colors"
          >
            <ArrowLeft className="h-5 w-5" />
          </button>
          <div>
            <p className="text-sm text-gray-400">{latest?.municipality_name}</p>
            <h1 className="mt-0.5 text-xl font-bold leading-snug text-gray-800">
              {latest?.theme}
            </h1>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2 pt-1">
          {latest && <StatusBadge status={latest.status} />}
          {isDraft && (
            <Button size="sm" onClick={handleSubmit}>
              <Send className="mr-1 h-3.5 w-3.5" />
              TL に提出
            </Button>
          )}
        </div>
      </div>

      {/* 元の入力内容 */}
      {root && <InputSummary proposal={root} />}

      {/* チェーン履歴 */}
      {chain.map((p, i) => {
        const versionNum = i + 1;
        const isLatestEntry = i === chain.length - 1;
        return (
          <div key={p.id}>
            {/* 指示ラベル（v1 以外） */}
            {p.refine_instruction && (
              <div className="flex items-start gap-2 px-3 py-2">
                <div className="mt-1 h-3.5 w-0.5 shrink-0 bg-gray-300" />
                <div className="rounded-lg bg-amber-50 border border-amber-200 px-3 py-2 text-sm">
                  <span className="font-medium text-amber-700">指示: </span>
                  <span className="text-amber-800">「{p.refine_instruction}」</span>
                </div>
              </div>
            )}
            <ProposalVersion proposal={p} versionNum={versionNum} isLatest={isLatestEntry} />
          </div>
        );
      })}

      {/* ストリーミング中 */}
      {(phase === "streaming" || phase === "selecting" || phase === "deepening") && streamText && (
        <div className="rounded-xl border border-primary-200 bg-white shadow-sm">
          <div className="flex items-center gap-2 border-b border-gray-100 px-5 py-3">
            {phase === "streaming" && (
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary-500" />
            )}
            <span className="text-sm font-medium text-gray-600">
              {phase === "streaming" ? "AI 生成中..." : "提案書（更新版）"}
            </span>
          </div>
          <div
            ref={streamRef}
            className="prose prose-sm max-w-none overflow-y-auto px-5 py-4"
            style={{ maxHeight: "55vh", whiteSpace: "pre-wrap", fontFamily: "inherit" }}
          >
            {streamText}
          </div>
        </div>
      )}

      {/* 施策選択 */}
      {phase === "selecting" && measures.length > 0 && (
        <MeasureSelector
          measures={measures}
          selected={selected}
          onToggle={toggleMeasure}
          onDeepen={handleDeepen}
          onSkip={() => { if (newId) router.push(`/proposals/${newId}`); }}
          loading={false}
        />
      )}

      {/* 深掘り中 */}
      {phase === "deepening" && (
        <div className="rounded-xl border border-primary-200 bg-white shadow-sm">
          <div className="flex items-center gap-2 border-b border-gray-100 px-5 py-3">
            <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary-500" />
            <span className="text-sm font-medium text-gray-600">詳細計画を生成中...</span>
          </div>
          <div
            ref={deepRef}
            className="prose prose-sm max-w-none overflow-y-auto px-5 py-4"
            style={{ maxHeight: "55vh", whiteSpace: "pre-wrap", fontFamily: "inherit" }}
          >
            {deepText || <span className="text-gray-400">生成中...</span>}
          </div>
        </div>
      )}

      {/* 指示入力パネル */}
      {phase === "idle" && latest && (
        <div>
          <div className="my-4 flex items-center gap-3">
            <div className="h-px flex-1 bg-gray-200" />
            <span className="flex items-center gap-1 text-xs text-gray-400">
              <Plus className="h-3 w-3" /> 次の指示
            </span>
            <div className="h-px flex-1 bg-gray-200" />
          </div>
          <InstructionPanel
            latestId={latest.id}
            onSend={handleInstruction}
            disabled={phase !== "idle"}
          />
        </div>
      )}
    </div>
  );
}
