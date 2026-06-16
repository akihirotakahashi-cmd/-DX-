"use client";

import { useState, useRef, useEffect, Suspense } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { useAuthStore } from "@/store/auth";

type Phase = "form" | "generating" | "selecting" | "deepening" | "done" | "error";

interface Measure {
  index: number;
  title: string;
}

const TEXTAREA_FIELDS = [
  { key: "futureVision",  label: "実現したい将来像", required: true  },
  { key: "currentState",  label: "現在像",           required: false },
  { key: "challenges",    label: "抱えている課題",   required: false },
  { key: "rootCauses",    label: "課題の原因",       required: false },
] as const;

type FormKey = (typeof TEXTAREA_FIELDS)[number]["key"];

const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000/api/v1";

/** SSE ストリームを読み込み、チャンクとイベントをコールバックに渡す */
async function readSse(
  res: Response,
  onChunk: (text: string) => void,
  onMeasures: (measures: Measure[]) => void,
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
      if (line.startsWith("event: ")) {
        pendingEvent = line.slice(7).trim();
        continue;
      }
      if (line === "") { pendingEvent = ""; continue; }
      if (!line.startsWith("data: ")) continue;

      const payload = line.slice(6);

      if (pendingEvent === "measures") {
        try { onMeasures(JSON.parse(payload)); } catch {}
        pendingEvent = "";
        continue;
      }
      if (/^[0-9a-f-]{36}$/.test(payload.trim())) {
        onDone(payload.trim());
        continue;
      }
      onChunk(payload.replace(/<br>/g, "\n"));
    }
  }
}

function NewProposalContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { idToken } = useAuthStore();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const previewRef  = useRef<HTMLDivElement>(null);
  const deepRef     = useRef<HTMLDivElement>(null);

  // ── フォーム状態
  const [fields, setFields] = useState<Record<FormKey, string>>({
    futureVision: "", currentState: "", challenges: "", rootCauses: "",
  });

  // URL パラメータから将来像を事前入力
  useEffect(() => {
    const fv = searchParams.get("future_vision");
    if (fv) setFields((f) => ({ ...f, futureVision: decodeURIComponent(fv) }));
  }, []);
  const [files, setFiles] = useState<File[]>([]);
  const [urls,  setUrls]  = useState<string[]>([""]);

  // ── 生成状態
  const [phase,        setPhase]        = useState<Phase>("form");
  const [initialText,  setInitialText]  = useState("");
  const [deepText,     setDeepText]     = useState("");
  const [measures,     setMeasures]     = useState<Measure[]>([]);
  const [selected,     setSelected]     = useState<Set<number>>(new Set());
  const [proposalId,   setProposalId]   = useState<string | null>(null);
  const [errorMsg,     setErrorMsg]     = useState("");

  const updateField = (key: FormKey, val: string) =>
    setFields((f) => ({ ...f, [key]: val }));

  const addUrl    = () => setUrls((u) => [...u, ""]);
  const removeUrl = (i: number) => setUrls((u) => u.filter((_, j) => j !== i));
  const updateUrl = (i: number, val: string) =>
    setUrls((u) => u.map((v, j) => (j === i ? val : v)));

  const onFilesSelected = (list: FileList | null) => {
    if (!list) return;
    setFiles((f) => [...f, ...Array.from(list)]);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };
  const removeFile = (i: number) => setFiles((f) => f.filter((_, j) => j !== i));

  const scrollBottom = (ref: React.RefObject<HTMLDivElement>) =>
    setTimeout(() => ref.current?.scrollTo({ top: ref.current.scrollHeight, behavior: "smooth" }), 10);

  // ── 初回提案生成
  const handleGenerate = async (e: React.FormEvent) => {
    e.preventDefault();
    setPhase("generating");
    setInitialText("");
    setMeasures([]);
    setSelected(new Set());

    const formData = new FormData();
    formData.append("future_vision", fields.futureVision);
    formData.append("current_state", fields.currentState);
    formData.append("challenges",    fields.challenges);
    formData.append("root_causes",   fields.rootCauses);
    urls.filter((u) => u.trim()).forEach((u) => formData.append("reference_urls", u));
    files.forEach((f) => formData.append("attachments", f));

    try {
      const res = await fetch(`${API}/proposals/stream`, {
        method: "POST",
        headers: { Authorization: `Bearer ${idToken}` },
        body: formData,
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      await readSse(
        res,
        (text) => { setInitialText((p) => p + text); scrollBottom(previewRef); },
        (m)    => { setMeasures(m); },
        (id)   => { setProposalId(id); setPhase("selecting"); },
      );
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "生成に失敗しました");
      setPhase("error");
    }
  };

  // ── 採用施策チェック切り替え
  const toggleMeasure = (idx: number) =>
    setSelected((s) => {
      const next = new Set(s);
      next.has(idx) ? next.delete(idx) : next.add(idx);
      return next;
    });

  // ── 深掘り生成
  const handleDeepen = async () => {
    if (selected.size === 0 || !proposalId) return;
    setPhase("deepening");
    setDeepText("");

    const body = {
      selected_measures: measures
        .filter((m) => selected.has(m.index))
        .map((m) => ({ index: m.index, title: m.title })),
      future_vision: fields.futureVision,
    };

    try {
      const res = await fetch(`${API}/proposals/${proposalId}/deepen`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          Authorization: `Bearer ${idToken}`,
        },
        body: JSON.stringify(body),
      });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      await readSse(
        res,
        (text) => { setDeepText((p) => p + text); scrollBottom(deepRef); },
        () => {},
        () => { setPhase("done"); },
      );
    } catch (err) {
      setErrorMsg(err instanceof Error ? err.message : "深掘りに失敗しました");
      setPhase("error");
    }
  };

  // ── TL 提出
  const handleSubmit = async () => {
    if (!proposalId) return;
    await fetch(`${API}/proposals/${proposalId}/submit`, {
      method: "POST",
      headers: { Authorization: `Bearer ${idToken}` },
    });
    router.push("/proposals");
  };

  const reset = () => {
    setPhase("form"); setInitialText(""); setDeepText("");
    setMeasures([]); setSelected(new Set()); setProposalId(null); setErrorMsg("");
  };

  // ────────────────────────────────────────────
  // レンダリング
  // ────────────────────────────────────────────
  return (
    <div className="mx-auto max-w-4xl space-y-6">
      <h1 className="text-2xl font-bold">新規提案生成</h1>

      {/* ── フォーム ── */}
      {phase === "form" && (
        <form onSubmit={handleGenerate} className="space-y-5">
          {/* 記入欄 */}
          <Card>
            <CardHeader><h2 className="font-semibold text-gray-800">記入欄</h2></CardHeader>
            <CardBody className="space-y-4">
              {TEXTAREA_FIELDS.map(({ key, label, required }) => (
                <div key={key}>
                  <label className="mb-1 block text-sm font-medium text-gray-700">
                    {label}{required && <span className="ml-1 text-red-500">*</span>}
                  </label>
                  <textarea
                    required={required}
                    rows={3}
                    value={fields[key]}
                    onChange={(e) => updateField(key, e.target.value)}
                    className="w-full resize-y rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
                  />
                </div>
              ))}
            </CardBody>
          </Card>

          {/* 添付 */}
          <Card>
            <CardHeader><h2 className="font-semibold text-gray-800">添付</h2></CardHeader>
            <CardBody>
              <input ref={fileInputRef} type="file" multiple className="hidden"
                onChange={(e) => onFilesSelected(e.target.files)} />
              <button type="button" onClick={() => fileInputRef.current?.click()}
                className="w-full rounded-md border border-dashed border-gray-300 px-4 py-3 text-center text-sm text-gray-500 transition-colors hover:border-primary-400 hover:text-primary-600">
                ＋ ファイルを追加（PDF / Word / Excel / PPT など）
              </button>
              {files.length > 0 && (
                <ul className="mt-3 space-y-1">
                  {files.map((f, i) => (
                    <li key={i} className="flex items-center justify-between rounded bg-gray-50 px-3 py-1.5 text-sm">
                      <span className="truncate text-gray-700">{f.name}</span>
                      <button type="button" onClick={() => removeFile(i)} className="ml-3 text-gray-400 hover:text-red-500">×</button>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>

          {/* 参照URL */}
          <Card>
            <CardHeader><h2 className="font-semibold text-gray-800">参照すべきURL</h2></CardHeader>
            <CardBody className="space-y-2">
              {urls.map((url, i) => (
                <div key={i} className="flex gap-2">
                  <input type="url" placeholder="https://..." value={url}
                    onChange={(e) => updateUrl(i, e.target.value)}
                    className="min-w-0 flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500" />
                  {urls.length > 1 && (
                    <button type="button" onClick={() => removeUrl(i)} className="shrink-0 px-2 text-gray-400 hover:text-red-500">×</button>
                  )}
                </div>
              ))}
              <button type="button" onClick={addUrl} className="text-sm text-primary-600 hover:underline">＋ URLを追加</button>
            </CardBody>
          </Card>

          <Button type="submit" className="w-full" size="lg">AI で提案書を生成する</Button>
        </form>
      )}

      {/* ── 生成中 ── */}
      {phase === "generating" && (
        <Card>
          <CardHeader>
            <h2 className="flex items-center gap-2 font-semibold">
              <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary-500" />
              AI 生成中...
            </h2>
          </CardHeader>
          <CardBody>
            <div ref={previewRef} className="prose prose-sm max-w-none overflow-y-auto rounded-md bg-gray-50 p-4"
              style={{ maxHeight: "60vh", whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
              {initialText || <span className="text-gray-400">生成中...</span>}
            </div>
          </CardBody>
        </Card>
      )}

      {/* ── 施策選択 ── */}
      {(phase === "selecting" || phase === "deepening" || phase === "done") && (
        <>
          {/* 初回提案書 */}
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <h2 className="font-semibold">提案書（初回）</h2>
                <Button variant="secondary" size="sm" onClick={reset}>再生成</Button>
              </div>
            </CardHeader>
            <CardBody>
              <div ref={previewRef} className="prose prose-sm max-w-none overflow-y-auto rounded-md bg-gray-50 p-4"
                style={{ maxHeight: "50vh", whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                {initialText}
              </div>
            </CardBody>
          </Card>

          {/* 施策選択パネル */}
          {measures.length > 0 && phase === "selecting" && (
            <Card>
              <CardHeader>
                <h2 className="font-semibold text-gray-800">採用する施策を選択してください</h2>
                <p className="mt-0.5 text-sm text-gray-500">チェックした施策について詳細実施計画（課題解決目標・定量分析・ロードマップ・出典）を生成します</p>
              </CardHeader>
              <CardBody className="space-y-2">
                {measures.map((m) => (
                  <label key={m.index}
                    className={`flex cursor-pointer items-center gap-3 rounded-lg border px-4 py-3 transition-colors ${
                      selected.has(m.index)
                        ? "border-primary-400 bg-primary-50"
                        : "border-gray-200 hover:border-gray-300"
                    }`}>
                    <input
                      type="checkbox"
                      checked={selected.has(m.index)}
                      onChange={() => toggleMeasure(m.index)}
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
                  <Button variant="secondary" onClick={handleSubmit}>
                    スキップして TL に提出
                  </Button>
                  <Button
                    onClick={handleDeepen}
                    disabled={selected.size === 0}
                  >
                    選択した施策を深掘りする（{selected.size}件）
                  </Button>
                </div>
              </CardBody>
            </Card>
          )}

          {/* 深掘り中 */}
          {(phase === "deepening" || phase === "done") && (
            <Card>
              <CardHeader>
                <h2 className="flex items-center gap-2 font-semibold">
                  {phase === "deepening" ? (
                    <>
                      <span className="inline-block h-2 w-2 animate-pulse rounded-full bg-primary-500" />
                      詳細計画を生成中...
                    </>
                  ) : (
                    "採用施策 詳細実施計画"
                  )}
                </h2>
              </CardHeader>
              <CardBody>
                <div ref={deepRef} className="prose prose-sm max-w-none overflow-y-auto rounded-md bg-gray-50 p-4"
                  style={{ maxHeight: "60vh", whiteSpace: "pre-wrap", fontFamily: "inherit" }}>
                  {deepText || <span className="text-gray-400">生成中...</span>}
                </div>

                {phase === "done" && (
                  <div className="mt-4 flex justify-end">
                    <Button onClick={handleSubmit}>TL レビューに提出</Button>
                  </div>
                )}
              </CardBody>
            </Card>
          )}
        </>
      )}

      {/* ── エラー ── */}
      {phase === "error" && (
        <Card>
          <CardBody>
            <p className="text-red-600">{errorMsg}</p>
            <Button variant="secondary" className="mt-3" onClick={reset}>戻る</Button>
          </CardBody>
        </Card>
      )}
    </div>
  );
}

export default function NewProposalPage() {
  return (
    <Suspense fallback={<div className="h-8 w-48 animate-pulse rounded bg-gray-200" />}>
      <NewProposalContent />
    </Suspense>
  );
}
