import { useState, useRef, useCallback } from "react";
import { usePDFUpload } from "@/hooks/usePDFUpload";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

interface PDFUploadProps {
  onExtracted?: (text: string) => void;
  onRemoved?: () => void;
}

export function PDFUpload({ onExtracted, onRemoved }: PDFUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const { file, isExtracting, error, handleFileSelect, removeFile } = usePDFUpload({
    onExtracted,
    onRemoved,
  });

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const droppedFile = e.dataTransfer.files[0];
      if (droppedFile) {
        handleFileSelect(droppedFile);
      }
    },
    [handleFileSelect]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const selectedFile = e.target.files?.[0];
      if (selectedFile) {
        handleFileSelect(selectedFile);
      }
    },
    [handleFileSelect]
  );

  const handleRemoveFile = useCallback(() => {
    removeFile();
    // Reset the file input so the same file can be selected again
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }, [removeFile]);

  const formatFileSize = (bytes: number): string => {
    return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
  };

  return (
    <div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {!file ? (
        <div
          onClick={() => fileInputRef.current?.click()}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          className={cn(
            "border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all",
            "bg-white/45 backdrop-blur-sm",
            "border-[#b3d1ff] shadow-[0_2px_12px_0_rgba(0,123,255,0.04)]",
            isDragging && "border-primary bg-primary/7",
            "hover:border-primary hover:bg-primary/7"
          )}
        >
          <div className="flex flex-col items-center gap-2">
            <div className="text-5xl opacity-50">📄</div>
            <p className="text-base text-[#495057] m-0">Drag & drop your PDF here</p>
            <p className="text-xs text-text-light m-0">Single PDF file, max 50MB</p>
          </div>
        </div>
      ) : (
        <div className="flex items-center justify-between p-4 border border-[#e0e0e0] rounded-xl bg-white/70 shadow-[0_2px_8px_0_rgba(0,0,0,0.04)] mt-2.5">
          <div className="flex items-center gap-3">
            <div className="text-2xl">📄</div>
            <div className="flex flex-col gap-0.5">
              <span className="font-medium text-[#343a40] text-sm">{file.name}</span>
              <span className="text-xs text-text-light">{formatFileSize(file.size)}</span>
            </div>
          </div>
          <Button
            type="button"
            variant="destructive"
            size="sm"
            onClick={handleRemoveFile}
            className="px-4 py-2 text-xs font-semibold"
          >
            Remove
          </Button>
        </div>
      )}

      {isExtracting && (
        <p className="mt-2 text-sm text-text-muted">
          [Extracting PDF text...]
        </p>
      )}

      {error && (
        <p className="mt-2 text-sm text-red-600">{error.message}</p>
      )}
    </div>
  );
}


