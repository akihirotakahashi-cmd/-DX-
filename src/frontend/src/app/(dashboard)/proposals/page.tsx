"use client";

import { useEffect, useState, Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Plus, ChevronDown, ChevronRight, Pencil, Eye, Send } from "lucide-react";
import api, { Proposal } from "@/lib/api";
import { toast } from "@/store/toast";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/Badge";

// ── ステータスの日本語ラベル
const STATUS_LABEL: Record<string, string> = {
  draft:          "下書き",
  reviewing_tl:   "TL確認中",
  reviewing_mgr:  "MGR確認中",
  approved:       "承認済み",
  rejected:       "差し戻し",
  cancelled:      "キャンセル",
  superseded:     "旧バージョン",
};

// ── テーマ別グループ型
interface ThemeGroup {
  theme: string;
  proposals: Proposal[];  // 新しい順
}

function groupByTheme(proposals: Proposal[]): ThemeGroup[] {
  const map = new Map<string, Proposal[]>();
  for (const p of proposals) {
    const key = p.theme;
    if (!map.has(key)) map.set(key, []);
    map.get(key)!.push(p);
  }
  return Array.from(map.entries())
    .map(([theme, ps]) => ({
      theme,
      proposals: ps.sort(
        (a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime()
      ),
    }))
    .sort(
      (a, b) =>
        new Date(b.proposals[0].created_at).getTime() -
        new Date(a.proposals[0].created_at).getTime()
    );
}

function ProposalsContent() {
  const searchParams = useSearchParams();
  const [groups, setGroups] = useState<ThemeGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    if (searchParams.get("submitted") === "1") toast.success("提案書を TL レビューに提出しました");
    if (searchParams.get("generated") === "1") toast.success("提案書を生成しました");
  }, []);

  useEffect(() => {
    api
      .get<Proposal[]>("/proposals")
      .then((r) => {
        const gs = groupByTheme(r.data);
        setGroups(gs);
        // 最初のグループは展開済みにする
        if (gs.length > 0) setExpanded(new Set([gs[0].theme]));
      })
      .finally(() => setLoading(false));
  }, []);

  const toggleExpand = (theme: string) =>
    setExpanded((s) => {
      const next = new Set(s);
      next.has(theme) ? next.delete(theme) : next.add(theme);
      return next;
    });

  const submitProposal = async (id: string) => {
    await api.post(`/proposals/${id}/submit`);
    toast.success("TL レビューに提出しました");
    // リロード
    const r = await api.get<Proposal[]>("/proposals");
    setGroups(groupByTheme(r.data));
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="h-8 w-48 animate-pulse rounded bg-gray-200" />
        <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
        <div className="h-32 animate-pulse rounded-lg bg-gray-100" />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* ヘッダー */}
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">施策提案</h1>
        <Link href="/proposals/new">
          <Button>
            <Plus className="mr-1.5 h-4 w-4" />
            新規テーマで提案を作成
          </Button>
        </Link>
      </div>

      {groups.length === 0 ? (
        <div className="rounded-lg border border-dashed border-gray-300 px-6 py-16 text-center">
          <p className="text-gray-400">まだ提案がありません</p>
          <Link href="/proposals/new" className="mt-3 inline-block text-sm text-primary-600 hover:underline">
            最初の提案を作成する
          </Link>
        </div>
      ) : (
        <div className="space-y-4">
          {groups.map((group) => {
            const isOpen = expanded.has(group.theme);
            const latest = group.proposals[0];

            return (
              <div key={group.theme} className="overflow-hidden rounded-xl border border-gray-200 bg-white shadow-sm">
                {/* テーマヘッダー */}
                <button
                  className="flex w-full items-start justify-between gap-4 px-5 py-4 text-left hover:bg-gray-50 transition-colors"
                  onClick={() => toggleExpand(group.theme)}
                >
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      {isOpen ? (
                        <ChevronDown className="h-4 w-4 shrink-0 text-gray-400" />
                      ) : (
                        <ChevronRight className="h-4 w-4 shrink-0 text-gray-400" />
                      )}
                      <span className="truncate font-semibold text-gray-800">{group.theme}</span>
                    </div>
                    <p className="ml-6 mt-0.5 text-xs text-gray-500">
                      {latest.municipality_name} ·{" "}
                      {group.proposals.length} バージョン ·{" "}
                      最終更新: {new Date(latest.updated_at).toLocaleDateString("ja-JP")}
                    </p>
                  </div>
                  <div className="shrink-0 mt-0.5">
                    <StatusBadge status={latest.status} />
                  </div>
                </button>

                {/* バージョン一覧 */}
                {isOpen && (
                  <div className="border-t border-gray-100">
                    {/* 新しいバージョン作成ボタン */}
                    <div className="flex justify-end border-b border-gray-100 bg-gray-50 px-5 py-2">
                      <Link
                        href={`/proposals/new?future_vision=${encodeURIComponent(group.theme)}`}
                        className="flex items-center gap-1 text-xs text-primary-600 hover:underline"
                      >
                        <Plus className="h-3 w-3" />
                        このテーマで新しいバージョンを作成
                      </Link>
                    </div>

                    <table className="w-full text-sm">
                      <thead className="bg-gray-50 text-left text-xs text-gray-500">
                        <tr>
                          <th className="px-5 py-2 font-medium">バージョン</th>
                          <th className="px-5 py-2 font-medium">作成日時</th>
                          <th className="px-5 py-2 font-medium">ステータス</th>
                          <th className="px-5 py-2 font-medium text-right">操作</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-gray-100">
                        {group.proposals.map((p, i) => {
                          const versionNum = group.proposals.length - i;
                          const isDraft = p.status === "draft" || p.status === "rejected";
                          return (
                            <tr
                              key={p.id}
                              className={`hover:bg-gray-50 transition-colors ${
                                p.status === "superseded" ? "opacity-50" : ""
                              }`}
                            >
                              <td className="px-5 py-3 font-medium text-gray-700">
                                v{versionNum}
                                {i === 0 && (
                                  <span className="ml-2 rounded bg-primary-100 px-1.5 py-0.5 text-xs font-medium text-primary-700">
                                    最新
                                  </span>
                                )}
                              </td>
                              <td className="px-5 py-3 text-gray-500">
                                {new Date(p.created_at).toLocaleString("ja-JP", {
                                  year: "numeric", month: "numeric", day: "numeric",
                                  hour: "2-digit", minute: "2-digit",
                                })}
                              </td>
                              <td className="px-5 py-3">
                                <StatusBadge status={p.status} />
                              </td>
                              <td className="px-5 py-3">
                                <div className="flex items-center justify-end gap-2">
                                  {isDraft ? (
                                    <>
                                      <Link href={`/proposals/${p.id}/edit`}>
                                        <button className="flex items-center gap-1 rounded border border-primary-300 bg-primary-50 px-3 py-1 text-xs font-medium text-primary-700 hover:bg-primary-100 transition-colors">
                                          <Pencil className="h-3 w-3" />
                                          編集
                                        </button>
                                      </Link>
                                      <button
                                        onClick={() => submitProposal(p.id)}
                                        className="flex items-center gap-1 rounded border border-gray-200 px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 transition-colors"
                                      >
                                        <Send className="h-3 w-3" />
                                        提出
                                      </button>
                                    </>
                                  ) : (
                                    <Link href={`/proposals/${p.id}`}>
                                      <button className="flex items-center gap-1 rounded border border-gray-200 px-3 py-1 text-xs text-gray-600 hover:bg-gray-100 transition-colors">
                                        <Eye className="h-3 w-3" />
                                        表示
                                      </button>
                                    </Link>
                                  )}
                                </div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function ProposalsPage() {
  return (
    <Suspense fallback={<div className="space-y-4"><div className="h-8 w-48 animate-pulse rounded bg-gray-200" /><div className="h-32 animate-pulse rounded-lg bg-gray-100" /></div>}>
      <ProposalsContent />
    </Suspense>
  );
}
