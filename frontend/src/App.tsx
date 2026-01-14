import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { ClerkProvider, useAuth } from "@clerk/clerk-react";
import { useEffect, useState, useLayoutEffect } from "react";
import { setClerkTokenGetter } from "./lib/api";
import AppLayout from "./components/layout/AppLayout";
import Dashboard from "./pages/Dashboard";
import CreateProject from "./pages/CreateProject";
import ProjectOverview from "./pages/ProjectOverview";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
    },
  },
});

// Check if running in test mode (set at build time) (This is needed for e2e tests)
const isTestMode = import.meta.env.VITE_TEST_MODE === 'true';

// Shared app routes component
function AppRoutes() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<AppLayout />}>
            <Route index element={<Dashboard />} />
            <Route path="create-project" element={<CreateProject />} />
            <Route path="project/:projectId" element={<ProjectOverview />} />
          </Route>
          <Route path="*" element={<div className="p-6">404 - Not Found</div>} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

function App() {
  // In test mode, skip Clerk entirely and go straight to app
  if (isTestMode) {
    return <AppWithoutAuth />;
  }

  const [clerkPublishableKey, setClerkPublishableKey] = useState<string | null>(null);
  const [configError, setConfigError] = useState<string | null>(null);

  useEffect(() => {
    // Fetch Clerk config from backend with retry logic
    let retries = 3;
    let delay = 1000;

    const fetchConfig = async (attempt: number) => {
      try {
        const response = await fetch("/api/clerk-config", {
          credentials: 'include',
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        if (data.publishableKey) {
          setClerkPublishableKey(data.publishableKey);
          setConfigError(null);
        } else {
          throw new Error("No publishable key in response");
        }
      } catch (err) {
        console.error(`Failed to load Clerk config (attempt ${attempt}):`, err);
        
        if (attempt < retries) {
          // Retry with exponential backoff
          setTimeout(() => fetchConfig(attempt + 1), delay);
          delay *= 2;
        } else {
          setConfigError(err instanceof Error ? err.message : "Failed to load Clerk configuration");
        }
      }
    };

    fetchConfig(1);
  }, []);

  // Show loading or error while fetching Clerk config
  if (!clerkPublishableKey) {
    return (
      <div className="flex flex-col items-center justify-center min-h-screen gap-4">
        {configError ? (
          <>
            <p className="text-red-600">Error: {configError}</p>
            <p className="text-text-muted text-sm">Make sure the backend is running on port 80</p>
            <button
              onClick={() => window.location.reload()}
              className="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-light"
            >
              Retry
            </button>
          </>
        ) : (
          <p className="text-text-muted">Loading Clerk configuration...</p>
        )}
      </div>
    );
  }

  return (
    <ClerkProvider 
      publishableKey={clerkPublishableKey}
    >
      <AppWithAuth />
    </ClerkProvider>
  );
}

// Inner component to access Clerk hooks
function AppWithAuth() {
  const { getToken, isLoaded } = useAuth();
  const [isTokenReady, setIsTokenReady] = useState(false);

  // Use layout effect to set token getter synchronously before render
  useLayoutEffect(() => {
    if (isLoaded && getToken) {
      setClerkTokenGetter(getToken);
      setIsTokenReady(true);
    }
  }, [getToken, isLoaded]);

  // Wait until Clerk is loaded and token getter is set
  if (!isLoaded || !isTokenReady) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <p className="text-text-muted">Loading authentication...</p>
      </div>
    );
  }

  return <AppRoutes />;
}

// App without authentication for test mode
function AppWithoutAuth() {
  // Set a mock token getter for test mode
  useLayoutEffect(() => {
    setClerkTokenGetter(async () => 'mock-test-token');
  }, []);

  return <AppRoutes />;
}

export default App;
