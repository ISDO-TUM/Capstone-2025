import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useCreateProject } from "@/hooks/useProjects";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { ProjectDescriptionTooltip } from "@/components/ui/tooltip";
import { PDFUpload } from "@/components/project/PDFUpload";

export default function CreateProject() {
  const navigate = useNavigate();
  const createProject = useCreateProject();
  
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [errors, setErrors] = useState<{ title?: string; description?: string }>({});

  const handlePDFExtracted = (extractedText: string) => {
    const currentText = description.trim();
    const newText = currentText
      ? `${currentText}\n\n${extractedText}`
      : extractedText;
    setDescription(newText);
  };

  const validateForm = (): boolean => {
    const newErrors: { title?: string; description?: string } = {};
    
    if (!title.trim()) {
      newErrors.title = "Project title is required";
    }
    
    if (!description.trim()) {
      newErrors.description = "Project description is required";
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!validateForm()) {
      return;
    }

    // Prevent duplicate submissions
    if (createProject.isPending) {
      return;
    }

    try {
      const result = await createProject.mutateAsync({
        title: title.trim(),
        description: description.trim(),
      });
      
      // Redirect to project overview with updateRecommendations flag
      navigate(`/project/${result.projectId}?updateRecommendations=true`);
    } catch (error) {
      console.error("Error creating project:", error);
      // Show user-friendly error message
      let errorMessage = "Failed to create project. Please try again.";
      
      if (error instanceof Error) {
        // Check for authentication errors
        if (error.message.includes("Not authenticated") || error.message.includes("401")) {
          errorMessage = "You must be signed in to create a project. Please sign in and try again.";
        } else if (error.message.includes("400")) {
          errorMessage = "Invalid project data. Please check your input and try again.";
        } else {
          errorMessage = error.message;
        }
      }
      
      // Show error to user (could be replaced with toast notification in future)
      alert(`Error: ${errorMessage}`);
    }
  };

  return (
    <main className="main-content">
      <div className="glass mx-auto my-8 px-11 py-12 max-w-3xl rounded-[28px] shadow-glass">
        <h1 className="mb-8 text-[2rem] font-bold text-[#1a237e] tracking-[0.5px]">
          Create New Project
        </h1>
        
        <form id="createProjectForm" onSubmit={handleSubmit} className="space-y-7">
          {/* Title Field */}
          <div className="form-group">
            <Label htmlFor="projectTitle" className="text-[1.08rem] font-semibold text-[#1a237e] mb-2">
              Project Title
            </Label>
            <Input
              id="projectTitle"
              name="projectTitle"
              type="text"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (errors.title) setErrors({ ...errors, title: undefined });
              }}
              required
              className={errors.title ? "border-red-500" : ""}
            />
            {errors.title && (
              <p className="text-sm text-red-600 mt-1">{errors.title}</p>
            )}
          </div>

          {/* Description Field */}
          <div className="form-group">
            <Label htmlFor="projectDescription" className="text-[1.08rem] font-semibold text-[#1a237e] mb-2 inline-flex items-center">
              Project Prompt
              <ProjectDescriptionTooltip />
            </Label>
            <Textarea
              id="projectDescription"
              name="projectDescription"
              rows={4}
              value={description}
              onChange={(e) => {
                setDescription(e.target.value);
                if (errors.description) setErrors({ ...errors, description: undefined });
              }}
              required
              className={errors.description ? "border-red-500" : ""}
              placeholder="Describe what kind of papers you're looking for..."
            />
            {errors.description && (
              <p className="text-sm text-red-600 mt-1">{errors.description}</p>
            )}
          </div>

          {/* PDF Upload Field */}
          <div className="form-group">
            <Label htmlFor="paperUpload" className="text-[1.08rem] font-semibold text-[#1a237e] mb-2">
              Upload Reference Paper (Optional)
            </Label>
            <p className="text-sm text-text-light mb-2.5">
              Upload a PDF to enhance your project recommendations
            </p>
            <PDFUpload onExtracted={handlePDFExtracted} />
          </div>

          {/* Submit Button */}
          <div className="flex justify-center">
            <Button
              type="submit"
              className="text-[1.13rem] px-10 py-4 rounded-[32px] max-w-[300px] w-full"
              disabled={createProject.isPending}
            >
              {createProject.isPending ? "Creating..." : "Get paper recommendations"}
            </Button>
          </div>
        </form>
      </div>
    </main>
  );
}
