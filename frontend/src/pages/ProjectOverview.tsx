import { useState, useMemo } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useRecommendationsStream } from "@/hooks/useRecommendationsStream";
import { PaperCard } from "@/components/project/PaperCard";

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
  const [searchParams] = useSearchParams();
  const queryClient = useQueryClient();
  
  const updateRecommendations = searchParams.get("updateRecommendations") === "true";
  
  const [searchQuery, setSearchQuery] = useState("");
  const [sortBy, setSortBy] = useState("");
  const [filterBy, setFilterBy] = useState("");
  const [replacementPapers, setReplacementPapers] = useState<Set<string>>(new Set());

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

  // Rate paper mutation
  const rateMutation = useMutation({
    mutationFn: ({ paperHash, rating }: { paperHash: string; rating: number }) =>
      ratePaper(projectId!, paperHash, rating),
    onSuccess: (data) => {
      // Handle replacement if returned
      if (data.replacement) {
        setReplacementPapers(prev => new Set(prev).add(data.replacement.paper.hash));
        // Remove highlight after 5 seconds
        setTimeout(() => {
          setReplacementPapers(prev => {
            const next = new Set(prev);
            next.delete(data.replacement.paper.paper_hash);
            return next;
          });
        }, 5000);
      }
      
      // Invalidate queries to refetch
      queryClient.invalidateQueries({ queryKey: ["recommendations", projectId] });
    },
  });

  // Filter and sort papers
  const filteredAndSortedPapers = useMemo(() => {
    let papers = [...recommendations];

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
  }, [recommendations, searchQuery, sortBy, filterBy]);

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

        {/* Agent Thoughts Section */}
        {thoughts.length > 0 && (
          <div className="agent-thoughts-section">
            <h2>Agent's Thoughts</h2>
            <ul className="agent-thoughts-list">
              {thoughts.map((thought, index) => (
                <li key={index}>
                  <strong>Step {index + 1}:</strong>
                  <p>{thought}</p>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Latest Papers Section - Placeholder for newsletter/pubsub papers */}
        <div className="recommendations-section">
          <h2>Latest Papers</h2>
          <div className="recommendations-grid">
            {/* Newsletter papers would go here */}
          </div>
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
                  />
                ))}
              </div>
              
              {/* Load More Button - Placeholder for future implementation */}
              <div className="load-more-container">
                <button 
                  className="load-more-btn" 
                  style={{ display: 'none' }}
                >
                  Load More
                </button>
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
