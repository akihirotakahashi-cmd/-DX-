"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { Amplify } from "aws-amplify";
import { Button } from "@/components/ui/Button";
import { Card, CardHeader, CardBody } from "@/components/ui/Card";

Amplify.configure({
  Auth: {
    Cognito: {
      userPoolId: process.env.NEXT_PUBLIC_COGNITO_USER_POOL_ID ?? "",
      userPoolClientId: process.env.NEXT_PUBLIC_COGNITO_CLIENT_ID ?? "",
    },
  },
});

const DEMO_MODE = process.env.NEXT_PUBLIC_DEMO_MODE === "true";

const DEMO_ACCOUNTS = [
  {
    email: "consultant@demo.jp",
    label: "コンサルタント",
    token: "demo-consultant",
    role: "consultant",
    tenantId: "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
  },
  {
    email: "tl@demo.jp",
    label: "チームリーダー",
    token: "demo-tl",
    role: "tl",
    tenantId: null,
  },
  {
    email: "manager@demo.jp",
    label: "マネージャー",
    token: "demo-manager",
    role: "manager",
    tenantId: null,
  },
] as const;

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const loginWithDemo = async (account: (typeof DEMO_ACCOUNTS)[number]) => {
    const { useAuthStore } = await import("@/store/auth");
    useAuthStore.getState().setAuth(account.token, account.email, account.role, account.tenantId);
    router.push("/proposals");
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      if (DEMO_MODE) {
        const account = DEMO_ACCOUNTS.find((a) => a.email === email);
        if (!account || password !== "Demo1234") {
          setError("メールまたはパスワードが正しくありません");
          return;
        }
        await loginWithDemo(account);
        return;
      }
      const { signIn } = await import("aws-amplify/auth");
      const { isSignedIn } = await signIn({ username: email, password });
      if (isSignedIn) {
        const { fetchAuthSession } = await import("aws-amplify/auth");
        const session = await fetchAuthSession();
        const idToken = session.tokens?.idToken?.toString() ?? "";
        const payload = session.tokens?.idToken?.payload;
        const { useAuthStore } = await import("@/store/auth");
        useAuthStore.getState().setAuth(
          idToken,
          payload?.email as string,
          payload?.["custom:role"] as string,
          (payload?.["custom:tenant_id"] as string) ?? null
        );
        router.push("/proposals");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "ログインに失敗しました");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-gray-50 p-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <h1 className="text-xl font-bold text-primary-700">地方創生DX</h1>
          <p className="mt-1 text-sm text-gray-500">ログイン</p>
        </CardHeader>
        <CardBody>
          {DEMO_MODE && (
            <div className="mb-4 rounded-lg border border-indigo-200 bg-indigo-50 p-3">
              <p className="mb-2 text-xs font-semibold text-indigo-700">
                デモアカウント（クリックで即ログイン）
              </p>
              <div className="flex flex-col gap-1.5">
                {DEMO_ACCOUNTS.map((account) => (
                  <button
                    key={account.email}
                    type="button"
                    onClick={() => loginWithDemo(account)}
                    className="flex items-center justify-between rounded border border-indigo-300 bg-white px-3 py-1.5 text-left text-xs text-indigo-800 hover:bg-indigo-100 transition-colors"
                  >
                    <span className="font-medium">{account.label}</span>
                    <span className="text-indigo-500">{account.email}</span>
                  </button>
                ))}
                <p className="mt-1 text-xs text-indigo-400">
                  パスワード入力の場合: <span className="font-mono">Demo1234</span>
                </p>
              </div>
            </div>
          )}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">メールアドレス</label>
              <input
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            <div>
              <label className="mb-1 block text-sm font-medium text-gray-700">パスワード</label>
              <input
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-primary-500 focus:outline-none focus:ring-1 focus:ring-primary-500"
              />
            </div>
            {error && <p className="text-sm text-red-600">{error}</p>}
            <Button type="submit" className="w-full" loading={loading}>
              ログイン
            </Button>
          </form>
        </CardBody>
      </Card>
    </div>
  );
}
