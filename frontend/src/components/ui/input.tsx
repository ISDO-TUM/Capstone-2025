import * as React from "react";
import { cn } from "@/lib/utils";

export interface InputProps
  extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className, type, ...props }, ref) => {
    return (
      <input
        type={type}
        className={cn(
          "flex w-full rounded-xl border-none bg-white/70 px-4 py-3 text-base text-text-primary shadow-md transition-all",
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
Input.displayName = "Input";

export { Input };

