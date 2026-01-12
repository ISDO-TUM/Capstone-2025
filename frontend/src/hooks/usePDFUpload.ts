import { useState, useCallback } from 'react';
import { pdfApi } from '@/lib/api';

export interface UsePDFUploadOptions {
  onExtracted?: (text: string) => void;
  onRemoved?: () => void;
}

/**
 * Hook for handling PDF file upload and text extraction
 */
export function usePDFUpload({ onExtracted, onRemoved }: UsePDFUploadOptions = {}) {
  const [file, setFile] = useState<File | null>(null);
  const [isExtracting, setIsExtracting] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const handleFileSelect = useCallback(
    (selectedFile: File) => {
      // Validate file type
      if (selectedFile.type !== 'application/pdf') {
        setError(new Error('Please select a PDF file only.'));
        return;
      }

      // Validate file size (50MB max)
      const maxSize = 50 * 1024 * 1024;
      if (selectedFile.size > maxSize) {
        setError(new Error('File size must be less than 50MB.'));
        return;
      }

      setFile(selectedFile);
      setError(null);
      setIsExtracting(true);

      // Extract PDF text
      pdfApi
        .extractText(selectedFile)
        .then((result) => {
          if (result.success && result.extracted_text) {
            if (onExtracted) {
              onExtracted(result.extracted_text);
            }
          } else {
            setError(new Error(result.error || 'Failed to extract PDF text'));
          }
        })
        .catch((err) => {
          setError(err instanceof Error ? err : new Error(String(err)));
        })
        .finally(() => {
          setIsExtracting(false);
        });
    },
    [onExtracted]
  );

  const removeFile = useCallback(() => {
    setFile(null);
    setError(null);
    if (onRemoved) {
      onRemoved();
    }
  }, [onRemoved]);

  return {
    file,
    isExtracting,
    error,
    handleFileSelect,
    removeFile,
  };
}

