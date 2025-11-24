import { useState } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Star } from "lucide-react";
import type { Paper } from "@/types";

interface PaperCardProps {
  paper: Paper;
  onRate: (paperHash: string, rating: number) => Promise<void>;
  isReplacement?: boolean;
}

export function PaperCard({ paper, onRate, isReplacement = false }: PaperCardProps) {
  const [currentRating, setCurrentRating] = useState(paper.rating || 0);
  const [isRating, setIsRating] = useState(false);

  const handleRatingClick = async (rating: number) => {
    if (isRating) return;
    
    setIsRating(true);
    setCurrentRating(rating);
    
    try {
      await onRate(paper.hash, rating);
    } catch (error) {
      console.error("Failed to rate paper:", error);
      // Revert rating on error
      setCurrentRating(paper.rating || 0);
    } finally {
      setIsRating(false);
    }
  };

  const formatFWCI = (fwci: number) => {
    return fwci < 10 ? fwci.toFixed(2) : Math.round(fwci).toString();
  };

  const getFWCIColor = (fwci: number) => {
    if (fwci >= 1.5) return "#28a745";
    if (fwci >= 1.0) return "#ffc107";
    return "#6c757d";
  };

  const getPercentileBadge = (percentile: any) => {
    if (!percentile || typeof percentile !== "object") return null;
    
    const value = Math.round(percentile.value * 100);
    
    if (percentile.is_in_top_1_percent) {
      return { color: "#dc3545", text: "TOP 1%", value };
    }
    if (percentile.is_in_top_10_percent) {
      return { color: "#ffc107", text: "TOP 10%", value };
    }
    
    return null;
  };

  const year = paper.publication_date 
    ? new Date(paper.publication_date).getFullYear() 
    : null;

  const pdfUrl = paper.pdf_url || (paper.is_oa && paper.oa_url ? paper.oa_url : null);
  const percentileBadge = getPercentileBadge(paper.citation_normalized_percentile);

  return (
    <Card
      className={`recommendation-card transition-all duration-300 ${
        isReplacement ? "animate-pulse bg-blue-50" : ""
      }`}
      data-paper-hash={paper.hash}
      data-title={paper.title.toLowerCase()}
      data-rating={currentRating}
      data-year={year || 0}
      data-citations={paper.cited_by_count || 0}
      data-fwci={paper.fwci || 0}
      data-percentile={percentileBadge?.value || 0}
    >
      <CardContent className="p-6">
        {/* Title Row with Metrics */}
        <div className="flex items-start justify-between gap-4 mb-3">
          <h3 className="text-xl font-bold text-text-primary flex-1 leading-tight">
            {paper.title}
          </h3>
          
          {/* Key Metrics */}
          <div className="flex gap-4 items-center flex-shrink-0">
            {/* FWCI */}
            {paper.fwci !== undefined && paper.fwci !== null && (
              <div className="text-center relative group cursor-help">
                <div className="text-[11px] font-semibold text-text-light uppercase tracking-wider">
                  FWCI
                </div>
                <div
                  className="text-lg font-bold"
                  style={{ color: getFWCIColor(paper.fwci) }}
                >
                  {formatFWCI(paper.fwci)}
                </div>
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                  Source: OpenAlex API<br />Field-Weighted Citation Impact
                </div>
              </div>
            )}

            {/* Citations */}
            {paper.cited_by_count !== undefined && paper.cited_by_count !== null && (
              <div className="text-center relative group cursor-help">
                <div className="text-[11px] font-semibold text-text-light uppercase tracking-wider">
                  Citations
                </div>
                <div className="text-lg font-bold text-text-primary">
                  {paper.cited_by_count}
                </div>
                <div className="absolute bottom-full left-1/2 transform -translate-x-1/2 mb-2 px-3 py-2 bg-gray-900 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap pointer-events-none z-10">
                  Source: OpenAlex API
                </div>
              </div>
            )}

            {/* Percentile Badge */}
            {percentileBadge && (
              <div className="text-center">
                <div
                  className="px-2.5 py-1 rounded text-[11px] font-bold"
                  style={{
                    background: percentileBadge.color,
                    color: percentileBadge.color === "#ffc107" ? "#212529" : "white",
                  }}
                >
                  {percentileBadge.text}
                </div>
                <div className="text-[11px] text-text-light mt-0.5">
                  {percentileBadge.value}th
                </div>
              </div>
            )}

            {/* Star Rating */}
            <div className="flex gap-1 pl-4 border-l-2 border-gray-200">
              {[1, 2, 3, 4, 5].map((star) => (
                <button
                  key={star}
                  type="button"
                  onClick={() => handleRatingClick(star)}
                  disabled={isRating}
                  className="transition-transform hover:scale-110 disabled:opacity-50"
                >
                  <Star
                    className={`w-5 h-5 ${
                      star <= currentRating
                        ? "fill-yellow-400 text-yellow-400"
                        : "text-gray-300"
                    }`}
                  />
                </button>
              ))}
            </div>
          </div>
        </div>

        {/* Description */}
        <p className="text-sm text-text-muted my-4 leading-relaxed">
          {paper.description}
        </p>

        {/* Metadata */}
        <div className="space-y-2 text-sm">
          {/* Authors */}
          {paper.authors && (
            <p className="flex items-center gap-2 text-text-secondary">
              <span className="text-base">👥</span>
              <span><strong>Authors:</strong> {paper.authors}</span>
            </p>
          )}

          {/* Year */}
          {year && (
            <p className="flex items-center gap-2 text-text-secondary">
              <span className="text-base">📅</span>
              <span><strong>Year:</strong> {year}</span>
            </p>
          )}

          {/* Venue */}
          {paper.venue_name && (
            <p className="flex items-center gap-2 text-text-secondary">
              <span className="text-base">🏛️</span>
              <span>
                <strong>Venue:</strong> {paper.venue_name}
                {paper.venue_type && (
                  <span className="text-text-light text-xs ml-1">
                    ({paper.venue_type})
                  </span>
                )}
              </span>
            </p>
          )}
        </div>

        {/* Access Links and Badges */}
        <div className="flex items-center gap-2 mt-4 flex-wrap">
          {/* Read Paper Link */}
          {paper.link && (
            <a
              href={paper.link}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 bg-gray-600 hover:bg-gray-700 text-white px-2.5 py-1 rounded text-xs font-semibold transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"></path>
                <polyline points="15 3 21 3 21 9"></polyline>
                <line x1="10" y1="14" x2="21" y2="3"></line>
              </svg>
              Read Paper
            </a>
          )}

          {/* Open Access Badge */}
          {paper.is_oa !== undefined && (
            <span
              className="inline-flex items-center px-2.5 py-1 rounded text-xs text-white"
              style={{ background: paper.is_oa ? "#28a745" : "#6c757d" }}
            >
              {paper.is_oa ? "🔓" : "🔒"}{" "}
              {paper.is_oa
                ? `Open Access${paper.oa_status ? ` (${paper.oa_status})` : ""}`
                : "Closed Access"}
            </span>
          )}

          {/* PDF Link */}
          {pdfUrl && (
            <a
              href={pdfUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-1.5 bg-blue-600 hover:bg-blue-700 text-white px-2.5 py-1 rounded text-xs font-semibold transition-colors"
            >
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path>
                <polyline points="14 2 14 8 20 8"></polyline>
                <line x1="16" y1="13" x2="8" y2="13"></line>
                <line x1="16" y1="17" x2="8" y2="17"></line>
                <polyline points="10 9 9 9 8 9"></polyline>
              </svg>
              PDF
            </a>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
