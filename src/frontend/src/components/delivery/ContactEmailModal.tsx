"use client";

import { useState } from "react";
import api from "@/lib/api";
import { Button } from "@/components/ui/Button";

interface Props {
  tenantId: string;
  currentEmail: string | null;
  onClose: () => void;
  onSaved: () => void;
}

export function ContactEmailModal({ tenantId, currentEmail, onClose, onSaved }: Props) {
  const [email, setEmail] = useState(currentEmail ?? "");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim()) return;
    setLoading(true);
    setError("");
    try {
      await api.patch(`/tenants/${tenantId}`, { contact_email: email });
      onSaved();
    } catch {
      setError("保存に失敗しました");
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40">
      <div className="w-full max-w-sm rounded-lg bg-white p-6 shadow-xl">
        <h2 className="text-lg font-semibold">担当者メールアドレス設定</h2>
        <p className="mt-1 text-sm text-gray-500">ポータルURLの送付先を設定します</p>
        <form onSubmit={handleSave} className="mt-4 space-y-4">
          <div>
            <label className="mb-1 block text-sm font-medium text-gray-700">メールアドレス</label>
            <input
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="contact@city.example.lg.jp"
              className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
            />
          </div>
          {error && <p className="text-sm text-red-600">{error}</p>}
          <div className="flex justify-end gap-3">
            <Button variant="secondary" type="button" onClick={onClose} disabled={loading}>
              キャンセル
            </Button>
            <Button type="submit" loading={loading}>
              保存
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
