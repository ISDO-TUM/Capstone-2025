import { useState, useCallback } from 'react';
import { streamSSE } from '@/lib/sse';
import type { Paper } from '@/types';

export interface UseLoadMorePapersOptions {
  projectId: string;
  onPapersLoaded?: (papers: Paper[]) => void;
}

/**
 * Hook for loading more papers via SSE stream
 */
export function useLoadMorePapers({ projectId, onPapersLoaded }: UseLoadMorePapersOptions) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const loadMore = useCallback(() => {
    if (!projectId || isLoading) return;

    setIsLoading(true);
    setError(null);

    const abortController = new AbortController();
    const newPapers: Paper[] = [];

    streamSSE('/api/load_more_papers', {
      method: 'POST',
      signal: abortController.signal,
      body: JSON.stringify({ project_id: projectId }),
      onMessage: (data: any) => {
        if (data.recommendations && Array.isArray(data.recommendations)) {
          newPapers.push(...data.recommendations);
          if (onPapersLoaded) {
            onPapersLoaded(data.recommendations);
          }
        }
      },
      onError: (err: Error) => {
        setError(err);
        setIsLoading(false);
      },
      onComplete: () => {
        setIsLoading(false);
      },
    });

    return () => {
      abortController.abort();
    };
  }, [projectId, isLoading, onPapersLoaded]);

  return {
    loadMore,
    isLoading,
    error,
  };
}

