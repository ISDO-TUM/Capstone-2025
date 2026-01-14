/**
 * API Client for Capstone Backend
 * All API endpoints are proxied through Vite dev server to http://localhost:80
 */

const API_BASE = '/api';

// Function to get Clerk token (will be set by ClerkProvider context)
let getToken: (() => Promise<string | null>) | null = null;

export function setClerkTokenGetter(tokenGetter: () => Promise<string | null>) {
  getToken = tokenGetter;
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorText = await response.text();
    let errorMessage = `HTTP ${response.status}: ${errorText}`;
    try {
      const errorJson = JSON.parse(errorText);
      errorMessage = errorJson.error || errorJson.message || errorMessage;
    } catch {
      // If not JSON, use the text as-is
    }
    throw new Error(errorMessage);
  }
  return response.json();
}

// Helper to create fetch options with Clerk token
async function getFetchOptions(options: RequestInit = {}): Promise<RequestInit> {
  const headers: HeadersInit = {
    ...options.headers,
  };

  // Clerk React SDK automatically sets cookies when user is signed in
  // The backend's authenticate_request reads from cookies, so we just need
  // to ensure credentials are included. We can also add the session token
  // as a fallback if the backend supports it.
  if (getToken) {
    try {
      const token = await getToken();
      if (token) {
        // Some backends support both cookie and header auth
        // Adding it as a fallback, but cookies should be primary
        (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
      }
    } catch (err) {
      // Token fetch failed, but cookies might still work
      console.warn('Failed to get Clerk token (cookies may still work):', err);
    }
  }

  return {
    ...options,
    headers,
    credentials: 'include', // Always include cookies
  };
}

// Projects API
export const projectsApi = {
  /**
   * Get all projects for the current user
   */
  async getAll(): Promise<{ success: boolean; projects?: any[]; error?: string }> {
    const fetchOptions = await getFetchOptions();
    const response = await fetch(`${API_BASE}/getProjects`, fetchOptions);
    return handleResponse(response);
  },

  /**
   * Get a single project by ID
   */
  async getById(projectId: string): Promise<{ title: string; description: string; project_id: string }> {
    const fetchOptions = await getFetchOptions();
    const response = await fetch(`${API_BASE}/project/${projectId}`, fetchOptions);
    return handleResponse(response);
  },

  /**
   * Create a new project
   */
  async create(data: { title: string; description: string }): Promise<{ projectId: string }> {
    const fetchOptions = await getFetchOptions({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const response = await fetch(`${API_BASE}/projects`, fetchOptions);
    return handleResponse(response);
  },

  /**
   * Update project prompt/description
   */
  async updatePrompt(projectId: string, prompt: string): Promise<{ description: string }> {
    const fetchOptions = await getFetchOptions({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ prompt }),
    });
    const response = await fetch(`${API_BASE}/project/${projectId}/update_prompt`, fetchOptions);
    return handleResponse(response);
  },
};

// PDF Extraction API
export const pdfApi = {
  /**
   * Extract text from uploaded PDF
   */
  async extractText(file: File): Promise<{ success: boolean; extracted_text?: string; error?: string }> {
    const formData = new FormData();
    formData.append('file', file);

    const fetchOptions = await getFetchOptions({
      method: 'POST',
      body: formData,
    });
    const response = await fetch(`${API_BASE}/extract-pdf-text`, fetchOptions);
    return handleResponse(response);
  },
};

// Paper Rating API
export const ratingApi = {
  /**
   * Rate a paper (1-5 stars)
   * Returns rating status and replacement info if applicable
   */
  async ratePaper(data: {
    paper_hash: string;
    rating: number;
    project_id: string;
  }): Promise<{
    status: string;
    message?: string;
    replacement?: {
      status: string;
      replacement_title?: string;
      replacement_paper_hash?: string;
      replacement_url?: string;
      replacement_summary?: string;
    };
  }> {
    const fetchOptions = await getFetchOptions({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
    });
    const response = await fetch(`${API_BASE}/rate_paper`, fetchOptions);
    return handleResponse(response);
  },
};

// PubSub/Newsletter API
export const pubsubApi = {
  /**
   * Update newsletter papers for a project
   */
  async updateNewsletterPapers(projectId: string): Promise<{ success?: boolean; error?: string }> {
    const fetchOptions = await getFetchOptions({
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ projectId }),
    });
    const response = await fetch(`${API_BASE}/pubsub/update_newsletter_papers`, fetchOptions);
    return handleResponse(response);
  },

  /**
   * Get newsletter papers for a project
   */
  async getNewsletterPapers(projectId: string): Promise<any[]> {
    const fetchOptions = await getFetchOptions();
    const response = await fetch(`${API_BASE}/pubsub/get_newsletter_papers?projectId=${projectId}`, fetchOptions);
    return handleResponse(response);
  },
};
