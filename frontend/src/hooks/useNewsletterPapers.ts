import { useQuery } from "@tanstack/react-query";
import type { Paper } from "@/types";

async function updateNewsletterPapers(projectId: string): Promise<void> {
  try {
    const response = await fetch('/api/pubsub/update_newsletter_papers', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ projectId }),
      credentials: 'include',
    });
    
    const result = await response.json();
    
    if (!response.ok) {
      console.warn('Update_newsletter_papers status failed:', response.status, result);
      // Don't throw for new projects without queries yet - this is expected
      if (response.status === 500 || (result.error && (
        result.error.includes('No search queries found') ||
        result.error.includes('queries') ||
        result.error.includes('query')
      ))) {
        return;
      }
    } else {
      // Small delay to ensure database commit
      await new Promise(resolve => setTimeout(resolve, 1000));
    }
  } catch (error) {
    console.warn('Error updating newsletter papers (non-fatal):', error);
    // Don't throw - this shouldn't block the page from loading
  }
}

async function fetchNewsletterPapers(projectId: string): Promise<Paper[]> {
  // First update the newsletter papers
  await updateNewsletterPapers(projectId);
  
  // Then fetch them
  const response = await fetch(`/api/pubsub/get_newsletter_papers?projectId=${projectId}`, {
    credentials: "include",
  });
  
  if (!response.ok) {
    throw new Error("Failed to fetch newsletter papers");
  }
  
  const papers = await response.json();
  return papers;
}

export function useNewsletterPapers(projectId: string | undefined, enabled = true) {
  return useQuery({
    queryKey: ["newsletter-papers", projectId],
    queryFn: () => fetchNewsletterPapers(projectId!),
    enabled: enabled && !!projectId,
    staleTime: 1000 * 60 * 5, // 5 minutes
    refetchOnWindowFocus: false,
  });
}
