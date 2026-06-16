"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import axios from "axios";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";
import { Download, FileText } from "lucide-react";

interface PortalProposal {
  municipality_name: string;
  theme: string;
  content_url: string | null;
}

type Phase = "loading" | "ready" | "error";

export default function PortalPage() {
  const { token } = useParams<{ token: string }>();
  const [data, setData] = useState<PortalProposal | null>(null);
  const [phase, setPhase] = useState<Phase>("loading");
  const [content, setContent] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [downloaded, setDownloaded] = useState(false);

  useEffect(() => {
    axios
      .get<PortalProposal>(`/api/v1/portal/${token}`)
      .then(async (r) => {
        setData(r.data);
        setPhase("ready");
        if (r.data.content_url) {
          // 提案書本文を取得して表示
          try {
            const text = await fetch(r.data.content_url).then((res) => res.text());
            setContent(text);
          } catch {
            // 本文取得失敗はサイレント（ダウンロードボタンは使える）
          }
        }
      })
      .catch(() => setPhase("error"));
  }, [token]);

  const handleDownload = async () => {
    if (!data?.content_url) return;
    setDownloading(true);
    try {
      // ダウンロード記録（冪等: DEC-008）
      await axios.post(`/api/v1/portal/${token}/download`);
      setDownloaded(true);

      // ファイルダウンロードを実行
      const res = await fetch(data.content_url);
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `proposal_${data.municipality_name}.md`;
      a.click();
      URL.revokeObjectURL(url);
    } finally {
      setDownloading(false);
    }
  };

  if (phase === "error") {
    return (
      <div className="flex min-h-screen flex-col items-center justify-center gap-3 bg-gray-50">
        <p className="text-lg font-medium text-gray-700">ページが見つかりません</p>
        <p className="text-sm text-gray-400">URLが無効か、削除された可能性があります。</p>
      </div>
    );
  }

  if (phase === "loading" || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-gray-50">
        <p className="text-gray-400">読み込み中...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* ヘッダー */}
      <header className="border-b border-gray-200 bg-white px-6 py-4">
        <p className="text-xs text-gray-400">地方創生DX 提案書ポータル</p>
        <div className="mt-1 flex items-center justify-between gap-4">
          <div>
            <h1 className="text-xl font-bold text-gray-900">{data.municipality_name} 様</h1>
            <p className="text-sm text-gray-600">{data.theme}</p>
          </div>
          {data.content_url && (
            <Button
              loading={downloading}
              onClick={handleDownload}
              className="flex-shrink-0"
            >
              <Download className="h-4 w-4" />
              {downloaded ? "再ダウンロード" : "提案書をダウンロード"}
            </Button>
          )}
        </div>
      </header>

      {/* 本文 */}
      <main className="mx-auto max-w-4xl p-6">
        {content ? (
          <Card>
            <CardHeader>
              <div className="flex items-center gap-2">
                <FileText className="h-4 w-4 text-gray-400" />
                <h2 className="font-semibold">提案書</h2>
              </div>
            </CardHeader>
            <CardBody>
              <div
                className="prose prose-sm max-w-none"
                style={{ whiteSpace: "pre-wrap", fontFamily: "inherit", lineHeight: 1.8 }}
              >
                {content}
              </div>
            </CardBody>
          </Card>
        ) : data.content_url ? (
          <Card>
            <CardBody>
              <p className="text-center text-sm text-gray-400">
                提案書を読み込んでいます...
              </p>
            </CardBody>
          </Card>
        ) : (
          <Card>
            <CardBody>
              <p className="text-center text-sm text-gray-400">
                提案書を準備中です。しばらくお待ちください。
              </p>
            </CardBody>
          </Card>
        )}

        <p className="mt-6 text-center text-xs text-gray-400">
          このURLは失効しません。大切に保管してください。
        </p>
      </main>
    </div>
  );
}
