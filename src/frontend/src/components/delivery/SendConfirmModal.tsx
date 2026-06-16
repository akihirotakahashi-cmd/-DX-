"use client";

import { useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Mail } from "lucide-react";

interface Props {
  proposalId: string;
  municipalityName: string;
  contactEmail: string;
  onClose: () => void;
  onSent: () => void;
}

export function SendConfirmModal({ proposalId, municipalityName, contactEmail, onClose, onSent }: Props) {
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    setLoading(true);
    await api.post(`/proposals/${proposalId}/send`);
    onSent();
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-xl">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-full bg-primary-100">
            <Mail className="h-5 w-5 text-primary-600" />
          </div>
          <h2 className="text-lg font-semibold">ポータル URL をメール送信</h2>
        </div>

        <div className="mt-4 rounded-md bg-gray-50 p-4 text-sm space-y-2">
          <div className="flex justify-between">
            <span className="text-gray-500">送付先</span>
            <span className="font-medium">{municipalityName} 担当者様</span>
          </div>
          <div className="flex justify-between">
            <span className="text-gray-500">メールアドレス</span>
            <span className="font-mono text-xs">{contactEmail}</span>
          </div>
        </div>

        <p className="mt-3 text-sm text-gray-600">
          上記のメールアドレスにポータルURLを送信します。送信後の取り消しはできません。
        </p>

        <div className="mt-6 flex justify-end gap-3">
          <Button variant="secondary" onClick={onClose} disabled={loading}>
            キャンセル
          </Button>
          <Button loading={loading} onClick={handleSend}>
            送信する
          </Button>
        </div>
      </div>
    </div>
  );
}
