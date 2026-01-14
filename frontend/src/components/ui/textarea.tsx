import * as React from "react";
import { cn } from "@/lib/utils";

export interface TextareaProps
  extends React.TextareaHTMLAttributes<HTMLTextAreaElement> {}

const Textarea = React.forwardRef<HTMLTextAreaElement, TextareaProps>(
  ({ className, ...props }, ref) => {
    return (
      <textarea
        className={cn(
          "flex min-h-[120px] w-full rounded-xl border-none bg-white/70 px-4 py-3 text-base text-text-primary shadow-md transition-all resize-vertical",
          "placeholder:text-text-light",
          "focus:bg-white/95 focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary/20",
          "hover:bg-white/85 hover:shadow-lg",
          className
        )}
        ref={ref}
        {...props}
      />
    );
  }
);
Textarea.displayName = "Textarea";

export { Textarea };

