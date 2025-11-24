import { useNavigate } from "react-router-dom";
import type { Project } from "@/types";

interface ProjectCardProps {
  project: Project;
  index: number;
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
  const animationDelay = `${index * 0.04 + 0.1}s`;
  const truncatedDescription = truncateText(project.description, 120);

  const handleClick = () => {
    if (project.project_id) {
      navigate(`/project/${project.project_id}`);
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
    </div>
  );
}

