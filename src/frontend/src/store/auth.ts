"use client";

import { create } from "zustand";
import { persist } from "zustand/middleware";

interface AuthState {
  idToken: string | null;
  email: string | null;
  role: string | null;
  tenantId: string | null;
  setAuth: (token: string, email: string, role: string, tenantId: string | null) => void;
  signOut: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      idToken: null,
      email: null,
      role: null,
      tenantId: null,
      setAuth: (idToken, email, role, tenantId) => set({ idToken, email, role, tenantId }),
      signOut: () => set({ idToken: null, email: null, role: null, tenantId: null }),
    }),
    { name: "auth-store" }
  )
);
