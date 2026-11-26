/**
 * Recipe 03.2: Production React SSE Streaming Hook with RAF Batching
 * Author: Vatsal Shah (Opportunity4u Press)
 * License: Apache-2.0
 */

import { useState, useRef, useCallback } from 'react';

export interface StreamState {
  isStreaming: boolean;
  content: string;
  error: string | null;
  outputTokens: number;
}

export function useClaudeStream() {
  const [state, setState] = useState<StreamState>({
    isStreaming: false,
    content: '',
    error: null,
    outputTokens: 0
  });

  const abortControllerRef = useRef<AbortController | null>(null);
  const pendingBufferRef = useRef<string>('');
  const rafIdRef = useRef<number | null>(null);

  const startStream = useCallback(async (prompt: string) => {
    // Abort existing stream if active
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();

    setState({ isStreaming: true, content: '', error: null, outputTokens: 0 });
    pendingBufferRef.current = '';

    // Schedule 60 FPS batched UI state commits
    const flushBufferToUI = () => {
      if (pendingBufferRef.current) {
        setState(prev => ({
          ...prev,
          content: prev.content + pendingBufferRef.current
        }));
        pendingBufferRef.current = '';
      }
      rafIdRef.current = requestAnimationFrame(flushBufferToUI);
    };
    rafIdRef.current = requestAnimationFrame(flushBufferToUI);

    try {
      const response = await fetch('/v1/chat/stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ prompt }),
        signal: abortControllerRef.current.signal
      });

      if (!response.ok || !response.body) {
        throw new Error(`HTTP error ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let partialLine = '';

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = (partialLine + chunk).split('\n');
        partialLine = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed.startsWith(':')) continue; // Skip comments/keepalives

          if (trimmed.startsWith('data: ')) {
            const dataStr = trimmed.slice(6);
            if (dataStr === '[DONE]') continue;

            try {
              const eventPayload = JSON.parse(dataStr);
              if (eventPayload.type === 'content_block_delta') {
                if (eventPayload.delta?.type === 'text_delta') {
                  pendingBufferRef.current += eventPayload.delta.text;
                }
              } else if (eventPayload.type === 'message_delta') {
                if (eventPayload.usage?.output_tokens) {
                  setState(prev => ({ ...prev, outputTokens: eventPayload.usage.output_tokens }));
                }
              }
            } catch (err) {
              console.warn('Skipping non-JSON data line:', dataStr);
            }
          }
        }
      }
    } catch (err: any) {
      if (err.name !== 'AbortError') {
        setState(prev => ({ ...prev, error: err.message }));
      }
    } finally {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
      // Final flush
      if (pendingBufferRef.current) {
        setState(prev => ({ ...prev, content: prev.content + pendingBufferRef.current }));
        pendingBufferRef.current = '';
      }
      setState(prev => ({ ...prev, isStreaming: false }));
    }
  }, []);

  const stopStream = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      abortControllerRef.current = null;
    }
  }, []);

  return { ...state, startStream, stopStream };
}
