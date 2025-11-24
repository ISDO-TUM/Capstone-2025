import { useState, useEffect, useCallback, useRef } from 'react';
import { streamSSE } from '@/lib/sse';
import type { Paper, RecommendationsResponse } from '@/types';

export interface UseRecommendationsStreamOptions {
  projectId: string;
  updateRecommendations?: boolean;
  enabled?: boolean;
}

export interface RecommendationsStreamState {
  thoughts: string[];
  recommendations: Paper[];
  isLoading: boolean;
  error: Error | null;
  outOfScope: RecommendationsResponse['out_of_scope'] | null;
  noResults: RecommendationsResponse['no_results'] | null;
}

/**
 * Hook for streaming recommendations from the backend
 * Handles SSE streaming and manages state for thoughts, recommendations, and errors
 */
export function useRecommendationsStream({
  projectId,
  updateRecommendations = false,
  enabled = true,
}: UseRecommendationsStreamOptions) {
  const [state, setState] = useState<RecommendationsStreamState>({
    thoughts: [],
    recommendations: [],
    isLoading: false,
    error: null,
    outOfScope: null,
    noResults: null,
  });

  const abortControllerRef = useRef<AbortController | null>(null);

  const startStream = useCallback(() => {
    if (!enabled || !projectId) return;

    // Abort any existing stream
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }

    const abortController = new AbortController();
    abortControllerRef.current = abortController;

    setState((prev) => ({
      ...prev,
      isLoading: true,
      error: null,
      thoughts: [],
      recommendations: [],
      outOfScope: null,
      noResults: null,
    }));

    streamSSE('/api/recommendations', {
      method: 'POST',
      signal: abortController.signal,
      body: JSON.stringify({
        projectId,
        update_recommendations: updateRecommendations,
      }),
      onMessage: (data: RecommendationsResponse) => {
        setState((prev) => {
          const newState = { ...prev };

          if (data.thought) {
            newState.thoughts = [...prev.thoughts, data.thought];
          }

          if (data.recommendations) {
            newState.recommendations = data.recommendations;
          }

          if (data.out_of_scope) {
            newState.outOfScope = data.out_of_scope;
            newState.recommendations = [];
          }

          if (data.no_results) {
            newState.noResults = data.no_results;
            newState.recommendations = [];
          }

          if (data.error) {
            newState.error = new Error(data.error);
            newState.isLoading = false;
          }

          return newState;
        });
      },
      onError: (error: Error) => {
        setState((prev) => ({
          ...prev,
          error,
          isLoading: false,
        }));
      },
      onComplete: () => {
        setState((prev) => ({
          ...prev,
          isLoading: false,
        }));
      },
    });
  }, [projectId, updateRecommendations, enabled]);

  useEffect(() => {
    if (enabled) {
      startStream();
    }

    return () => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
      }
    };
  }, [startStream, enabled]);

  return {
    ...state,
    restart: startStream,
  };
}
