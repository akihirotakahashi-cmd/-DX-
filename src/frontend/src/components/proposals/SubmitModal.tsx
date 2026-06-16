"use client";

import { useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface Props {
  proposalId: string;
  onClose: () => void;
  onSubmitted: () => void;
}

export function SubmitModal({ proposalId, onClose, onSubmitted }: Props) {
  const [loading, setLoading] = useState(false);

  const handleSubmit = async () => {
    setLoading(true);
    await api.post(`/proposals/${proposalId}/submit`);
    onSubmitted();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold">TL レビューに提出</h2>
        <p className="mt-2 text-sm text-gray-600">
          この提案書をチームリーダーのレビューに提出します。提出後は編集できません。
        </p>
        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            キャンセル
          </Button>
          <Button loading={loading} onClick={handleSubmit}>
            提出する
          </Button>
        </div>
      </div>
    </div>
  );
}
