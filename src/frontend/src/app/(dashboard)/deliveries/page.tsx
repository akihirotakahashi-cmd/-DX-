"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api, { DeliveryItem } from "@/lib/api";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { CheckCircle, XCircle, ChevronRight } from "lucide-react";

const StatusIcon = ({ ok }: { ok: boolean }) =>
  ok ? <CheckCircle className="h-4 w-4 text-green-500" /> : <XCircle className="h-4 w-4 text-gray-300" />;

export default function DeliveriesPage() {
  const [items, setItems] = useState<DeliveryItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<DeliveryItem[]>("/deliveries").then((r) => {
      setItems(r.data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">納品管理</h1>

      <Card>
        <CardHeader>
          <p className="text-sm text-gray-500">承認済み提案 {items.length} 件</p>
        </CardHeader>
        <CardBody className="p-0">
          {loading ? (
            <p className="px-6 py-8 text-center text-gray-400">読み込み中...</p>
          ) : items.length === 0 ? (
            <p className="px-6 py-8 text-center text-gray-400">承認済み提案がありません</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs text-gray-500">
                <tr>
                  <th className="px-6 py-3 font-medium">自治体</th>
                  <th className="px-6 py-3 font-medium">テーマ</th>
                  <th className="px-6 py-3 font-medium">承認日</th>
                  <th className="px-6 py-3 font-medium">URL発行</th>
                  <th className="px-6 py-3 font-medium">送信</th>
                  <th className="px-6 py-3 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">{item.municipality_name}</td>
                    <td className="px-6 py-4 font-medium">{item.theme}</td>
                    <td className="px-6 py-4 text-gray-500">
                      {item.approved_at
                        ? new Date(item.approved_at).toLocaleDateString("ja-JP")
                        : "—"}
                    </td>
                    <td className="px-6 py-4">
                      <StatusIcon ok={item.portal_issued} />
                    </td>
                    <td className="px-6 py-4">
                      <StatusIcon ok={item.portal_sent} />
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/proposals/${item.id}/delivery`}
                        className="flex items-center gap-1 text-primary-600 hover:underline"
                      >
                        納品準備
                        <ChevronRight className="h-4 w-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </CardBody>
      </Card>
    </div>
  );
}
