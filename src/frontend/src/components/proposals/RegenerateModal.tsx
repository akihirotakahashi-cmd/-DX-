"use client";

import { useState } from "react";
import api, { ProposalRead } from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface Props {
  proposalId: string;
  currentTheme: string;
  onClose: () => void;
  onRegenerated: (newId: string) => void;
}

export function RegenerateModal({ proposalId, currentTheme, onClose, onRegenerated }: Props) {
  const [theme, setTheme] = useState(currentTheme);
  const [loading, setLoading] = useState(false);

  const handleRegenerate = async () => {
    setLoading(true);
    const res = await api.post<ProposalRead>(`/proposals/${proposalId}/regenerate`, { theme });
    onRegenerated(res.data.id);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold">提案書を再生成</h2>
        <p className="mt-1 text-sm text-gray-500">
          テーマを変更して再生成できます。現在の下書きは差し替え済みになります（DEC-022）。
        </p>
        <div className="mt-4">
          <label className="mb-1 block text-sm font-medium text-gray-700">テーマ</label>
          <input
            type="text"
            maxLength={200}
            value={theme}
            onChange={(e) => setTheme(e.target.value)}
            className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
          />
        </div>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            キャンセル
          </Button>
          <Button loading={loading} onClick={handleRegenerate} disabled={!theme.trim()}>
            再生成する
          </Button>
        </div>
      </div>
    </div>
  );
}
