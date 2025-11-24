/**
 * Clerk Configuration
 * 
 * In development, we need to get the Clerk publishable key.
 * The backend provides this, but for now we'll use an environment variable
 * or fetch it from the backend.
 */

// For now, we'll fetch the publishable key from the backend
// In production, this could be set via environment variable
export async function getClerkPublishableKey(): Promise<string | null> {
  try {
    // Try to get from environment variable first (if set in Vite)
    const envKey = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY;
    if (envKey) {
      return envKey;
    }
    
    // Otherwise, we'll need to get it from the backend
    // For now, return null and we'll handle it in the component
    return null;
  } catch {
    return null;
  }
}

// Clerk Frontend API URL - same approach
export async function getClerkFrontendApiUrl(): Promise<string | null> {
  try {
    const envUrl = import.meta.env.VITE_CLERK_FRONTEND_API_URL;
    if (envUrl) {
      return envUrl;
    }
    return null;
  } catch {
    return null;
  }
}

