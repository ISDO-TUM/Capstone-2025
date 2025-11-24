import * as React from "react";
import { cn } from "@/lib/utils";

export interface LabelProps
  extends React.LabelHTMLAttributes<HTMLLabelElement> {}

const Label = React.forwardRef<HTMLLabelElement, LabelProps>(
  ({ className, ...props }, ref) => {
    return (
      <label
        ref={ref}
        className={cn(
          "text-base font-semibold text-text-primary mb-2 block",
          className
        )}
        {...props}
      />
    );
  }
);
Label.displayName = "Label";

export { Label };

