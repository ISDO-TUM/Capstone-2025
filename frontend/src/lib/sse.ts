/**
 * Server-Sent Events (SSE) utilities for streaming recommendations
 */

export interface SSEMessage<T = any> {
  type?: string;
  data?: T;
}

export interface SSEOptions {
  onMessage?: (data: any) => void;
  onError?: (error: Error) => void;
  onComplete?: () => void;
}

/**
 * Parse SSE data format: "data: {json}\n\n"
 */
function parseSSELine(line: string): any | null {
  if (line.startsWith('data: ')) {
    const jsonString = line.substring(6).trim();
    if (jsonString) {
      try {
        return JSON.parse(jsonString);
      } catch (e) {
        console.warn('Failed to parse SSE data:', jsonString, e);
        return null;
      }
    }
  }
  return null;
}

/**
 * Stream SSE response from fetch API
 * Handles the streaming format used by the backend recommendations endpoint
 */
export async function streamSSE(
  url: string,
  options: RequestInit & SSEOptions
): Promise<void> {
  const { onMessage, onError, onComplete, ...fetchOptions } = options;

  try {
    const response = await fetch(url, {
      ...fetchOptions,
      headers: {
        'Content-Type': 'application/json',
        ...fetchOptions.headers,
      },
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`SSE request failed: ${response.status} ${errorText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();

        if (done) {
          // Process any remaining data in buffer
          if (buffer.trim() && onMessage) {
            const lines = buffer.split('\n\n');
            for (const line of lines) {
              const data = parseSSELine(line);
              if (data) {
                onMessage(data);
              }
            }
          }
          if (onComplete) {
            onComplete();
          }
          break;
        }

        // Decode chunk and add to buffer
        buffer += decoder.decode(value, { stream: true });

        // Process complete messages (separated by \n\n)
        const lines = buffer.split('\n\n');
        // Keep the last incomplete line in buffer
        buffer = lines.pop() || '';

        for (const line of lines) {
          const data = parseSSELine(line);
          if (data && onMessage) {
            onMessage(data);
          }
        }
      }
    } finally {
      reader.releaseLock();
    }
  } catch (error) {
    if (onError) {
      onError(error instanceof Error ? error : new Error(String(error)));
    } else {
      throw error;
    }
  }
}

