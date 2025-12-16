import { useNavigate } from "react-router-dom";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import type { Project } from "@/types";

interface ProjectCardProps {
  project: Project;
  index: number;
}

async function deleteProject(projectId: string): Promise<void> {
  const response = await fetch(`/api/project/${projectId}`, {
    method: "DELETE",
    credentials: "include",
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || "Failed to delete project");
  }
}

/**
 * Formats date with CET timezone (+2 hours) and human-readable format
 */
function formatDate(dateString: string): string {
  const d = new Date(dateString);
  if (isNaN(d.getTime())) return dateString;
  
  // Add 2 hours for CET
  d.setHours(d.getHours() + 2);
  
  return d.toLocaleString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

/**
 * Truncates text to maxLength, adding "..." if needed
 */
function truncateText(text: string, maxLength: number): string {
  if (!text) return '';
  if (text.length <= maxLength) return text;
  return text.slice(0, maxLength - 3).trim() + '...';
}

export function ProjectCard({ project, index }: ProjectCardProps) {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const animationDelay = `${index * 0.04 + 0.1}s`;
  const truncatedDescription = truncateText(project.description, 120);

  const deleteMutation = useMutation({
    mutationFn: deleteProject,
    onSuccess: () => {
      // Invalidate projects query to refetch the list
      queryClient.invalidateQueries({ queryKey: ["projects"] });
    },
    onError: (error: Error) => {
      alert(`Failed to delete project: ${error.message}`);
    },
  });

  const handleClick = () => {
    if (project.project_id) {
      navigate(`/project/${project.project_id}`);
    }
  };

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent card click navigation
    
    if (confirm(`Are you sure you want to delete "${project.title}"? This action cannot be undone.`)) {
      deleteMutation.mutate(project.project_id);
    }
  };

  return (
    <div
      onClick={handleClick}
      className="project-card"
      style={{ 
        animationDelay,
      }}
    >
      <div className="project-title">
        {project.title}
      </div>
      
      <div className="project-description">
        {truncatedDescription}
      </div>
      
      {project.tags && project.tags.length > 0 && (
        <div className="project-tags">
          {project.tags.map((tag, idx) => (
            <span
              key={idx}
              className="project-tag"
            >
              {tag}
            </span>
          ))}
        </div>
      )}
      
      <div className="project-date">
        Created: {formatDate(project.date)}
      </div>

      <button
        onClick={handleDelete}
        className="delete-project-btn"
        title="Delete project"
        aria-label="Delete project"
        disabled={deleteMutation.isPending}
      >
        {deleteMutation.isPending ? (
          <span>...</span>
        ) : (
          <svg 
            width="16" 
            height="16" 
            viewBox="0 0 16 16" 
            fill="currentColor"
          >
            <path d="M5.5 5.5A.5.5 0 0 1 6 6v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm2.5 0a.5.5 0 0 1 .5.5v6a.5.5 0 0 1-1 0V6a.5.5 0 0 1 .5-.5zm3 .5a.5.5 0 0 0-1 0v6a.5.5 0 0 0 1 0V6z"/>
            <path fillRule="evenodd" d="M14.5 3a1 1 0 0 1-1 1H13v9a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V4h-.5a1 1 0 0 1-1-1V2a1 1 0 0 1 1-1H6a1 1 0 0 1 1-1h2a1 1 0 0 1 1 1h3.5a1 1 0 0 1 1 1v1zM4.118 4 4 4.059V13a1 1 0 0 0 1 1h6a1 1 0 0 0 1-1V4.059L11.882 4H4.118zM2.5 3V2h11v1h-11z"/>
          </svg>
        )}
      </button>
    </div>
  );
}

