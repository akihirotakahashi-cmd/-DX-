"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import api, { ReviewItem } from "@/lib/api";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { StatusBadge } from "@/components/ui/Badge";
import { ChevronRight } from "lucide-react";

export default function ReviewsPage() {
  const [items, setItems] = useState<ReviewItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    api.get<ReviewItem[]>("/reviews").then((r) => {
      setItems(r.data);
      setLoading(false);
    });
  }, []);

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">承認フロー</h1>

      <Card>
        <CardHeader>
          <p className="text-sm text-gray-500">レビュー待ち {items.length} 件</p>
        </CardHeader>
        <CardBody className="p-0">
          {loading ? (
            <p className="px-6 py-8 text-center text-gray-400">読み込み中...</p>
          ) : items.length === 0 ? (
            <p className="px-6 py-8 text-center text-gray-400">レビュー待ち案件はありません</p>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-left text-xs text-gray-500">
                <tr>
                  <th className="px-6 py-3 font-medium">自治体</th>
                  <th className="px-6 py-3 font-medium">テーマ</th>
                  <th className="px-6 py-3 font-medium">ステータス</th>
                  <th className="px-6 py-3 font-medium">提出日</th>
                  <th className="px-6 py-3 font-medium" />
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((item) => (
                  <tr key={item.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4">{item.municipality_name}</td>
                    <td className="px-6 py-4 font-medium">{item.theme}</td>
                    <td className="px-6 py-4">
                      <StatusBadge status={item.status} />
                    </td>
                    <td className="px-6 py-4 text-gray-500">
                      {new Date(item.created_at).toLocaleDateString("ja-JP")}
                    </td>
                    <td className="px-6 py-4">
                      <Link
                        href={`/reviews/${item.id}`}
                        className="flex items-center gap-1 text-primary-600 hover:underline"
                      >
                        審査する
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
