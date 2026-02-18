"use client";

import { QueryClient, QueryClientProvider, MutationCache } from "@tanstack/react-query";
import { useState } from "react";
import { Toaster, toast } from "sonner";
import { AuthContext, useAuthProvider } from "@/hooks/use-auth";

function AuthProvider({ children }: { children: React.ReactNode }) {
  const auth = useAuthProvider();
  return <AuthContext.Provider value={auth}>{children}</AuthContext.Provider>;
}

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        defaultOptions: {
          queries: {
            staleTime: 30 * 1000,
            retry: 1,
            refetchOnWindowFocus: false,
          },
        },
        mutationCache: new MutationCache({
          onError: (error) => {
            if (error instanceof Error) {
              toast.error(error.message);
            }
          },
        }),
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        {children}
        <Toaster
          position="bottom-right"
          richColors
          closeButton
          toastOptions={{
            duration: 4000,
          }}
        />
      </AuthProvider>
    </QueryClientProvider>
  );
}
