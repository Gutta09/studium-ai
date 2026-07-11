import { useState, type ReactNode } from "react";
import { AuthContext } from "./auth-context";
import { setAuthToken } from "./api/studium";

const TOKEN_KEY = "studium_token";
const EMAIL_KEY = "studium_email";

// Restore the token into the axios layer on module load (page refresh)
setAuthToken(localStorage.getItem(TOKEN_KEY));

export function AuthProvider({ children }: { children: ReactNode }) {
  const [email, setEmail] = useState<string | null>(() => localStorage.getItem(EMAIL_KEY));

  function signIn(token: string, userEmail: string) {
    localStorage.setItem(TOKEN_KEY, token);
    localStorage.setItem(EMAIL_KEY, userEmail);
    setAuthToken(token);
    setEmail(userEmail);
  }

  function signOut() {
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(EMAIL_KEY);
    setAuthToken(null);
    setEmail(null);
  }

  return (
    <AuthContext.Provider value={{ email, isAuthed: email !== null, signIn, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}
