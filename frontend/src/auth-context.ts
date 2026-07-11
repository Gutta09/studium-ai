import { createContext, useContext } from "react";

export interface AuthState {
  email: string | null;
  isAuthed: boolean;
  signIn: (token: string, email: string) => void;
  signOut: () => void;
}

export const AuthContext = createContext<AuthState | null>(null);

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside <AuthProvider>");
  return ctx;
}
