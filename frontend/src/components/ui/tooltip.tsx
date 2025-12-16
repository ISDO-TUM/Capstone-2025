import * as React from "react";
import { cn } from "@/lib/utils";

export interface TooltipProps {
  content: React.ReactNode;
  children: React.ReactElement;
  side?: "top" | "bottom" | "left" | "right";
  className?: string;
}

export function Tooltip({ content, children, side = "top", className }: TooltipProps) {
  const [isVisible, setIsVisible] = React.useState(false);

  return (
    <span
      className="relative inline-block cursor-pointer"
      onMouseEnter={() => setIsVisible(true)}
      onMouseLeave={() => setIsVisible(false)}
      onFocus={() => setIsVisible(true)}
      onBlur={() => setIsVisible(false)}
      tabIndex={0}
      role="button"
      aria-label="Show tooltip"
    >
      {children}
      {isVisible && (
        <div
          className={cn(
            "absolute z-50 rounded-xl p-4 text-[0.95em] font-normal leading-relaxed",
            "w-[320px] bg-[rgba(255,255,255,0.95)] text-[#1a237e]",
            "text-left backdrop-blur-md",
            "shadow-[0_4px_24px_0_rgba(31,38,135,0.15)] border-[1.5px] border-[#b3d1ff]",
            "transition-opacity duration-200",
            side === "top" && "bottom-full left-1/2 -translate-x-1/2 mb-2",
            side === "bottom" && "top-full left-1/2 -translate-x-1/2 mt-2",
            side === "left" && "right-full top-1/2 -translate-y-1/2 mr-2",
            side === "right" && "left-full top-1/2 -translate-y-1/2 ml-2",
            className
          )}
          role="tooltip"
        >
          {content}
        </div>
      )}
    </span>
  );
}

/**
 * Specialized tooltip for project description field
 * Shows filter explanations matching the old design
 */
export function ProjectDescriptionTooltip() {
  return (
    <Tooltip
      side="right"
      content={
        <div className="space-y-3">
          <div className="mb-4">
            <div className="text-[#1a237e] font-semibold text-[1.05em] mb-2">Example:</div>
            <div className="text-[#1a237e] italic">
              "I am looking for papers in the field of machine learning in healthcare published after 2018."
            </div>
          </div>
          <div>
            <div className="text-[#1a237e] font-semibold text-[1.05em] mb-2">
              You can use natural language filters in your prompt:
            </div>
          </div>
          <div className="space-y-2.5 mt-3">
            <div>
              <div className="text-[#1a237e] font-semibold mb-1">Authors</div>
              <div className="text-[#4a5568] text-[0.93em] leading-relaxed pl-2">
                Filter by specific authors of the paper.
              </div>
            </div>
            <div>
              <div className="text-[#1a237e] font-semibold mb-1">Publication Date</div>
              <div className="text-[#4a5568] text-[0.93em] leading-relaxed pl-2">
                The year or date when the paper was published.
              </div>
            </div>
            <div>
              <div className="text-[#1a237e] font-semibold mb-1">Field-Weighted Citation Impact (FWCI)</div>
              <div className="text-[#4a5568] text-[0.93em] leading-relaxed pl-2">
                A metric that shows how well-cited a paper is compared to others in its field (1.0 = world average).
              </div>
            </div>
            <div>
              <div className="text-[#1a237e] font-semibold mb-1">Citation Normalized Percentile</div>
              <div className="text-[#4a5568] text-[0.93em] leading-relaxed pl-2">
                Indicates the paper's citation performance as a percentile among similar papers (higher is better).
              </div>
            </div>
            <div>
              <div className="text-[#1a237e] font-semibold mb-1">Cited By Count</div>
              <div className="text-[#4a5568] text-[0.93em] leading-relaxed pl-2">
                The total number of times this paper has been cited by other works.
              </div>
            </div>
            <div>
              <div className="text-[#1a237e] font-semibold mb-1">Counts By Year</div>
              <div className="text-[#4a5568] text-[0.93em] leading-relaxed pl-2">
                Shows how many times the paper was cited in each year since publication.
              </div>
            </div>
            <div>
              <div className="text-[#1a237e] font-semibold mb-1">Similarity Score</div>
              <div className="text-[#4a5568] text-[0.93em] leading-relaxed pl-2">
                A score indicating how closely the paper matches your search or interests (higher means more relevant).
              </div>
            </div>
          </div>
        </div>
      }
    >
      <span className="ml-2 text-base align-middle cursor-pointer" aria-label="Show filter help">
        ℹ️
      </span>
    </Tooltip>
  );
}

