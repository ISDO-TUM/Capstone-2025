import { useState, useMemo, useEffect, useRef } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation } from "@tanstack/react-query";
import { useRecommendationsStream } from "@/hooks/useRecommendationsStream";
import { useNewsletterPapers } from "@/hooks/useNewsletterPapers";
import { useLoadMorePapers } from "@/hooks/useLoadMorePapers";
import { PaperCard } from "@/components/project/PaperCard";
import type { Paper } from "@/types";

interface Project {
  project_id: string;
  title: string;
  description: string;
}

async function fetchProject(projectId: string): Promise<Project> {
  const response = await fetch(`/api/project/${projectId}`, {
    credentials: "include",
  });
  if (!response.ok) throw new Error("Failed to fetch project");
  return response.json();
}

async function ratePaper(projectId: string, paperHash: string, rating: number) {
  const response = await fetch("/api/rate_paper", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    credentials: "include",
    body: JSON.stringify({
      project_id: projectId,
      paper_hash: paperHash,
      rating,
    }),
  });
  
  if (!response.ok) throw new Error("Failed to rate paper");
  return response.json();
}

export default function ProjectOverview() {
  const { projectId } = useParams<{ projectId: string }>();
  const [searchParams, setSearchParams] = useSearchParams();
  
  const updateRecommendations = searchParams.get("updateRecommendations") === "true";
  
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [filterBy, setFilterBy] = useState("");
  const [replacementPapers, setReplacementPapers] = useState<Set<string>>(new Set());
  const [additionalPapers, setAdditionalPapers] = useState<Paper[]>([]);
  const [replacedPapers, setReplacedPapers] = useState<Map<string, Paper>>(new Map());
  const [removedPapers, setRemovedPapers] = useState<Set<string>>(new Set());
  const [fadingOutPapers, setFadingOutPapers] = useState<Set<string>>(new Set());

  // Fetch project details
  const { data: project, isLoading: projectLoading } = useQuery({
    queryKey: ["project", projectId],
    queryFn: () => fetchProject(projectId!),
    enabled: !!projectId,
  });

  // Stream recommendations
  const {
    thoughts,
    recommendations,
    isLoading: streamLoading,
    error: streamError,
    outOfScope,
    noResults,
  } = useRecommendationsStream({
    projectId: projectId!,
    updateRecommendations,
    enabled: !!projectId,
  });

  // Fetch newsletter papers - only after recommendations have loaded
  const { data: newsletterPapers = [], isLoading: newsletterLoading } = useNewsletterPapers(
    projectId,
    recommendations.length > 0 || !streamLoading
  );

  // Load More Papers hook
  const { loadMore, isLoading: isLoadingMore, error: loadMoreError } = useLoadMorePapers({
    projectId: projectId!,
    onPapersLoaded: (newPapers) => {
      setAdditionalPapers(prev => [...prev, ...newPapers]);
    },
  });

  // Remove updateRecommendations param from URL after stream completes
  // This prevents re-running the agent on page refresh
  const hasRemovedParam = useRef(false);
  
  useEffect(() => {
    if (!updateRecommendations || hasRemovedParam.current || streamLoading) {
      return;
    }
    
    // Only remove the param AFTER stream has completely finished
    if (recommendations.length > 0 || thoughts.length > 0) {
      hasRemovedParam.current = true;
      searchParams.delete("updateRecommendations");
      setSearchParams(searchParams, { replace: true });
    }
  }, [updateRecommendations, streamLoading, recommendations.length, thoughts.length, searchParams, setSearchParams]);

  // Rate paper mutation
  const rateMutation = useMutation({
    mutationFn: ({ paperHash, rating }: { paperHash: string; rating: number }) =>
      ratePaper(projectId!, paperHash, rating),
    onSuccess: (data, variables) => {
      console.log('Rating response:', data);
      console.log('Variables:', variables);
      
      // Handle replacement if returned (rating 1-2)
      if (data.replacement && data.replacement.status === 'success') {
        const replacement = data.replacement;
        console.log('Replacement data:', replacement);
        
        const replacementPaper: Paper = {
          hash: replacement.replacement_paper_hash,
          title: replacement.replacement_title,
          description: replacement.replacement_summary,
          link: replacement.replacement_url,
          is_replacement: true,
          rating: 0,
          authors: replacement.replacement_authors,
          publication_date: replacement.replacement_publication_date,
          fwci: replacement.replacement_fwci,
          cited_by_count: replacement.replacement_cited_by_count,
          venue_name: replacement.replacement_venue_name,
          is_oa: replacement.replacement_is_oa,
          oa_status: replacement.replacement_oa_status,
          pdf_url: replacement.replacement_pdf_url,
        };
        
        console.log('Created replacement paper:', replacementPaper);
        
        // Start fade out animation
        setFadingOutPapers(prev => new Set(prev).add(variables.paperHash));
        
        // After fade out, replace the paper
        setTimeout(() => {
          // Store the replacement mapping
          setReplacedPapers(prev => {
            const newMap = new Map(prev).set(variables.paperHash, replacementPaper);
            console.log('Updated replacedPapers map:', Array.from(newMap.entries()));
            return newMap;
          });
          
          // Remove from fading out
          setFadingOutPapers(prev => {
            const next = new Set(prev);
            next.delete(variables.paperHash);
            return next;
          });
          
          // Add to replacement tracking for highlighting
          setReplacementPapers(prev => new Set(prev).add(replacementPaper.hash));
          
          // Remove highlight after 5 seconds
          setTimeout(() => {
            setReplacementPapers(prev => {
              const next = new Set(prev);
              next.delete(replacementPaper.hash);
              return next;
            });
          }, 5000);
        }, 500); // Wait for fade out animation
      } else if (variables.rating <= 2) {
        // Rating is 1-2 but no replacement found - remove the paper
        console.log('No replacement found (low rating), removing paper:', variables.paperHash);
        
        // Start fade out animation
        setFadingOutPapers(prev => new Set(prev).add(variables.paperHash));
        
        // After fade out, remove the paper
        setTimeout(() => {
          setRemovedPapers(prev => new Set(prev).add(variables.paperHash));
          setFadingOutPapers(prev => {
            const next = new Set(prev);
            next.delete(variables.paperHash);
            return next;
          });
        }, 500); // Wait for fade out animation
      }
    },
  });

  // Filter and sort papers (including loaded additional papers)
  const filteredAndSortedPapers = useMemo(() => {
    // Apply replacements to recommendations and filter out removed papers
    let papers = [...recommendations
      .filter(p => !removedPapers.has(p.hash))
      .map(p => replacedPapers.get(p.hash) || p), 
      ...additionalPapers.filter(p => !removedPapers.has(p.hash))];

    // Apply search filter
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase();
      papers = papers.filter(p => 
        p.title.toLowerCase().includes(query) ||
        p.description?.toLowerCase().includes(query) ||
        p.authors?.toLowerCase().includes(query)
      );
    }

    // Apply rating filter
    if (filterBy === "rated") {
      papers = papers.filter(p => p.rating && p.rating > 0);
    } else if (filterBy === "unrated") {
      papers = papers.filter(p => !p.rating || p.rating === 0);
    } else if (filterBy === "open-access") {
      papers = papers.filter(p => p.is_oa);
    } else if (filterBy === "closed-access") {
      papers = papers.filter(p => !p.is_oa);
    }

    // Apply sorting
    if (sortBy === "title") {
      papers.sort((a, b) => a.title.localeCompare(b.title));
    } else if (sortBy === "rating") {
      papers.sort((a, b) => (b.rating || 0) - (a.rating || 0));
    } else if (sortBy === "year") {
      papers.sort((a, b) => {
        const yearA = a.publication_date ? new Date(a.publication_date).getFullYear() : 0;
        const yearB = b.publication_date ? new Date(b.publication_date).getFullYear() : 0;
        return yearB - yearA;
      });
    } else if (sortBy === "citations") {
      papers.sort((a, b) => (b.cited_by_count || 0) - (a.cited_by_count || 0));
    } else if (sortBy === "fwci") {
      papers.sort((a, b) => (b.fwci || 0) - (a.fwci || 0));
    } else if (sortBy === "percentile") {
      papers.sort((a, b) => {
        const pctA = typeof a.citation_normalized_percentile === "object" 
          ? a.citation_normalized_percentile.value || 0 
          : 0;
        const pctB = typeof b.citation_normalized_percentile === "object"
          ? b.citation_normalized_percentile.value || 0
          : 0;
        return pctB - pctA;
      });
    } else if (sortBy === "oa") {
      papers.sort((a, b) => (b.is_oa ? 1 : 0) - (a.is_oa ? 1 : 0));
    }

    return papers;
  }, [recommendations, additionalPapers, searchQuery, sortBy, filterBy, replacedPapers, removedPapers]);

  const handleRatePaper = async (paperHash: string, rating: number) => {
    await rateMutation.mutateAsync({ paperHash, rating });
  };

  if (projectLoading) {
    return (
      <main className="main-content">
        <div className="flex min-h-[60vh] items-center justify-center">
          <p className="text-text-muted">Loading project...</p>
        </div>
      </main>
    );
  }

  if (!project) {
    return (
      <main className="main-content">
        <div className="flex min-h-[60vh] items-center justify-center">
          <p className="text-error">Project not found</p>
        </div>
      </main>
    );
  }

  return (
    <main className="main-content">
      <div className="container">
        {/* Project Header */}
        <div className="project-header">
          <h1>{project.title}</h1>
          <div className="description-wrapper">
            <div className="description-content">
              {project.description}
            </div>
          </div>
        </div>

        {/* Agent Thoughts Section - Only show when streaming or has thoughts */}
        {(streamLoading || thoughts.length > 0) && (
          <div className="agent-thoughts-section">
            <h2>Agent's Thoughts</h2>
            <ul className="agent-thoughts-list">
              {streamLoading && thoughts.length === 0 && (
                <li>🧠 Processing user input...</li>
              )}
              {thoughts.map((thought, index) => {
                // Determine icon based on thought content
                let icon = '🧠';
                let content = thought;
                
                if (content.includes('Calling tool:')) {
                  icon = '🛠️';
                } else if (content.includes('Tool response')) {
                  icon = '✅';
                } else if (content.includes('user input')) {
                  icon = '👤';
                } else if (content.includes('Final response')) {
                  icon = '🏁';
                } else if (content.includes('Checking')) {
                  icon = '🧠';
                } else if (content.includes('Extracted keywords')) {
                  icon = '🧠';
                } else if (content.includes('Performing')) {
                  icon = '🧠';
                } else if (content.includes('Updating')) {
                  icon = '🧠';
                }
                
                return (
                  <li key={index}>
                    {icon} {content}
                  </li>
                );
              })}
            </ul>
          </div>
        )}

        {/* Latest Papers Section - Newsletter/PubSub papers */}
        <div className="recommendations-section">
          <h2>Latest Papers</h2>
          {newsletterLoading ? (
            <p className="no-papers-message">Loading latest papers...</p>
          ) : newsletterPapers.length > 0 ? (
            <div className="latest-papers-grid">
              {newsletterPapers.map((paper) => (
                <PaperCard
                  key={paper.hash}
                  paper={paper}
                  onRate={handleRatePaper}
                  isReplacement={false}
                />
              ))}
            </div>
          ) : streamLoading ? (
            <p className="no-papers-message">Latest papers will appear after recommendations are generated...</p>
          ) : (
            <p className="no-papers-message">No latest papers available yet. Refresh the page after recommendations are generated.</p>
          )}
        </div>

        {/* Recommendations Section */}
        <div className="recommendations-section">
          <h2>Recommendations</h2>

          {/* Search Panel - Only show when there are recommendations */}
          {recommendations.length > 0 && (
            <div className="search-panel">
              <div className="search-controls-container">
                {/* Search Input */}
                <div className="search-input-wrapper">
                  <input
                    type="text"
                    placeholder="Search papers by title..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="search-input"
                  />
                </div>

                {/* Sort Dropdown */}
                <div className="sort-dropdown">
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value)}
                    className="sort-select"
                  >
                    <option value="">Sort papers</option>
                    <option value="title">Sort by Title</option>
                    <option value="rating">Sort by Rating</option>
                    <option value="year">Sort by Year</option>
                    <option value="citations">Sort by Citations</option>
                    <option value="fwci">Sort by FWCI</option>
                    <option value="percentile">Sort by Percentile</option>
                    <option value="oa">Open Access First</option>
                  </select>
                </div>

                {/* Filter Dropdown */}
                <div className="filter-dropdown">
                  <select
                    value={filterBy}
                    onChange={(e) => setFilterBy(e.target.value)}
                    className="filter-select"
                  >
                    <option value="">Filter papers</option>
                    <option value="rated">Rated Papers</option>
                    <option value="unrated">Unrated Papers</option>
                    <option value="open-access">Open Access Only</option>
                    <option value="closed-access">Closed Access Only</option>
                  </select>
                </div>
              </div>

              <div className="results-count">
                <span>{filteredAndSortedPapers.length} papers found</span>
              </div>
            </div>
          )}

          {/* Loading State */}
          {streamLoading && recommendations.length === 0 && (
            <div className="flex min-h-[40vh] items-center justify-center">
              <p className="text-text-muted">Loading recommendations...</p>
            </div>
          )}

          {/* Error State */}
          {streamError && (
            <div className="glass p-6 rounded-lg border-l-4 border-red-500">
              <p className="text-error">{streamError.message}</p>
            </div>
          )}

          {/* Papers Grid */}
          {filteredAndSortedPapers.length > 0 && (
            <>
              <div className="recommendations-grid">
                {filteredAndSortedPapers.map((paper) => (
                  <PaperCard
                    key={paper.hash}
                    paper={paper}
                    onRate={handleRatePaper}
                    isReplacement={replacementPapers.has(paper.hash)}
                    isFadingOut={fadingOutPapers.has(paper.hash)}
                  />
                ))}
              </div>
              
              {/* Load More Button */}
              <div className="load-more-container">
                <button 
                  className="load-more-btn"
                  onClick={loadMore}
                  disabled={isLoadingMore}
                >
                  {isLoadingMore ? 'Loading...' : 'Load More'}
                </button>
                {loadMoreError && (
                  <p style={{ color: '#dc3545', textAlign: 'center', marginTop: '8px' }}>
                    Failed to load more papers. Please try again.
                  </p>
                )}
              </div>
            </>
          )}

          {/* No Results */}
          {!streamLoading && recommendations.length > 0 && filteredAndSortedPapers.length === 0 && (
            <div style={{ padding: '2rem', textAlign: 'center' }}>
              <p style={{ color: '#6c757d' }}>No papers match your filters</p>
            </div>
          )}

          {/* Out of Scope / No Results Messages */}
          {outOfScope && (
            <div style={{ padding: '1.5rem', marginTop: '1rem', backgroundColor: '#fff3cd', borderLeft: '4px solid #ffc107', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 'bold', color: '#856404', marginBottom: '0.5rem' }}>Out of Scope</h3>
              <p style={{ color: '#856404' }}>{JSON.stringify(outOfScope)}</p>
            </div>
          )}

          {noResults && (
            <div style={{ padding: '1.5rem', marginTop: '1rem', backgroundColor: '#f8d7da', borderLeft: '4px solid #dc3545', borderRadius: '8px' }}>
              <h3 style={{ fontSize: '1.125rem', fontWeight: 'bold', color: '#721c24', marginBottom: '0.5rem' }}>No Results Found</h3>
              <p style={{ color: '#721c24' }}>{JSON.stringify(noResults)}</p>
            </div>
          )}
        </div>
      </div>
    </main>
  );
}
