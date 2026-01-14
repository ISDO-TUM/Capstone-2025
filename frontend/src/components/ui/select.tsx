import * as React from "react";
import { cn } from "@/lib/utils";

export interface SelectProps
  extends React.SelectHTMLAttributes<HTMLSelectElement> {
  onValueChange?: (value: string) => void;
}

const Select = React.forwardRef<HTMLSelectElement, SelectProps>(
  ({ className, children, onValueChange, ...props }, ref) => {
    return (
      <select
        className={cn(
          "flex w-full rounded-xl border-none bg-white/70 px-4 py-3 text-base text-text-primary shadow-md transition-all appearance-none cursor-pointer",
          "focus:bg-white/95 focus:shadow-lg focus:outline-none focus:ring-2 focus:ring-primary/20",
          "hover:bg-white/85 hover:shadow-lg",
          className
        )}
        ref={ref}
        onChange={(e) => {
          props.onChange?.(e);
          onValueChange?.(e.target.value);
        }}
        {...props}
      >
        {children}
      </select>
    );
  }
);
Select.displayName = "Select";

// Compatibility wrappers for Radix-style API
const SelectTrigger = Select;
const SelectContent = ({ children }: { children: React.ReactNode }) => <>{children}</>;
const SelectValue = ({ placeholder }: { placeholder?: string }) => <option value="">{placeholder}</option>;
const SelectItem = ({ value, children }: { value: string; children: React.ReactNode }) => (
  <option value={value}>{children}</option>
);

export { Select, SelectTrigger, SelectContent, SelectValue, SelectItem };

