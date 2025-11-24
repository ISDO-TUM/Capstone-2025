import { useState, useEffect, useMemo, useRef } from "react";
import { useAuth } from "@clerk/clerk-react";
import { SignIn } from "@clerk/clerk-react";
import { useProjects } from "@/hooks/useProjects";
import { ProjectCard } from "@/components/project/ProjectCard";
import type { Project } from "@/types";

/**
 * Filters projects by search query (title, description, tags)
 */
function filterProjectsBySearch(projects: Project[], searchValue: string): Project[] {
  const val = searchValue.trim().toLowerCase();
  if (!val) return projects;
  
  return projects.filter((p) => {
    const titleMatch = p.title?.toLowerCase().includes(val);
    const descMatch = p.description?.toLowerCase().includes(val);
    const tagsMatch = Array.isArray(p.tags) && 
      p.tags.some((tag) => tag?.toLowerCase().includes(val));
    
    return titleMatch || descMatch || tagsMatch;
  });
}

/**
 * Sorts projects by date (newest first)
 */
function sortProjectsByDate(projects: Project[]): Project[] {
  return [...projects].sort((a, b) => {
    const dateA = new Date(a.date).getTime();
    const dateB = new Date(b.date).getTime();
    return dateB - dateA;
  });
}

export default function Dashboard() {
  const { isSignedIn, isLoaded } = useAuth();
  const { data: projects = [], isLoading, error } = useProjects();
  const [searchQuery, setSearchQuery] = useState("");
  const [isSearchResult, setIsSearchResult] = useState(false);
  const projectsListRef = useRef<HTMLDivElement>(null);

  // Filter and sort projects
  const filteredProjects = useMemo(() => {
    const filtered = filterProjectsBySearch(projects, searchQuery);
    return sortProjectsByDate(filtered);
  }, [projects, searchQuery]);

  // Track if this is a search result
  useEffect(() => {
    setIsSearchResult(searchQuery.trim().length > 0);
  }, [searchQuery]);

  // Scroll animation setup using IntersectionObserver
  useEffect(() => {
    if (!projectsListRef.current) return;

    const cardContainers = projectsListRef.current.querySelectorAll('[data-project-card]');
    
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const cardElement = entry.target.querySelector('.project-card') as HTMLElement;
            if (cardElement) {
              cardElement.style.opacity = "1";
              cardElement.style.transform = "translateY(0) scale(1)";
            }
          }
        });
      },
      { threshold: 0.12 }
    );

    cardContainers.forEach((container) => {
      observer.observe(container);
    });

    return () => {
      cardContainers.forEach((container) => observer.unobserve(container));
    };
  }, [filteredProjects]);

  // Show empty state when no projects (and not searching)
  const showEmptyState = projects.length === 0 && !isSearchResult;
  // Show no results message when searching but no matches
  const showNoResults = isSearchResult && filteredProjects.length === 0;
  // Show search bar when there are projects or when searching
  const showSearchBar = projects.length > 0 || isSearchResult;

  // Show loading while Clerk is initializing
  if (!isLoaded) {
    return (
      <main className="main-content">
        <div className="flex min-h-[60vh] items-center justify-center">
          <p className="text-text-muted">Loading...</p>
        </div>
      </main>
    );
  }

  // Show sign-in if not authenticated
  if (!isSignedIn) {
    return (
      <main className="main-content">
        <div className="flex min-h-[60vh] items-center justify-center">
          <SignIn />
        </div>
      </main>
    );
  }

  if (isLoading) {
    return (
      <main className="main-content">
        <div className="flex min-h-[60vh] items-center justify-center">
          <p className="text-text-muted">Loading projects...</p>
        </div>
      </main>
    );
  }

  if (error) {
    return (
      <main className="main-content">
        <div className="container mx-auto px-4 py-8">
          <div className="text-center text-red-600">
            Error loading projects: {error.message}
          </div>
        </div>
      </main>
    );
  }

  return (
    <main className="main-content">
      {/* Search Bar */}
      {showSearchBar && (
        <div className="search-bar-wrapper">
          <input
            type="text"
            placeholder="Search by tag or keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="search-bar"
          />
        </div>
      )}

      {/* Empty State - No Projects */}
      {showEmptyState && (
        <div className="no-projects-container">
          <div className="no-projects-icon">📁</div>
          <h2 className="no-projects-title">
            There are no projects yet.
          </h2>
          <p className="no-projects-subtitle">
            Start your first project to begin exploring research papers and getting personalized recommendations.
          </p>
        </div>
      )}

      {/* Projects List */}
      {!showEmptyState && (
        <div
          ref={projectsListRef}
          className="projects-list"
        >
          {showNoResults ? (
            <div className="col-span-2 text-center text-text-light py-10 text-lg">
              No projects found matching your search.
            </div>
          ) : (
            filteredProjects.map((project, idx) => (
              <div key={project.project_id} data-project-card>
                <ProjectCard project={project} index={idx} />
              </div>
            ))
          )}
        </div>
      )}

    </main>
  );
}
