import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { projectsApi } from '@/lib/api';
import type { Project } from '@/types';

/**
 * Hook to fetch all projects
 */
export function useProjects() {
  return useQuery<Project[]>({
    queryKey: ['projects'],
    queryFn: async () => {
      const response = await projectsApi.getAll();
      if (response.success) {
        // Return empty array if projects is undefined or null
        return response.projects || [];
      }
      throw new Error(response.error || 'Failed to fetch projects');
    },
  });
}

/**
 * Hook to fetch a single project by ID
 */
export function useProject(projectId: string | undefined) {
  return useQuery({
    queryKey: ['project', projectId],
    queryFn: async () => {
      if (!projectId) throw new Error('Project ID is required');
      return projectsApi.getById(projectId);
    },
    enabled: !!projectId,
  });
}

/**
 * Hook to create a new project
 */
export function useCreateProject() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { title: string; description: string }) =>
      projectsApi.create(data),
    onSuccess: () => {
      // Invalidate projects list to refetch
      queryClient.invalidateQueries({ queryKey: ['projects'] });
    },
  });
}

/**
 * Hook to update project prompt
 */
export function useUpdateProjectPrompt(projectId: string) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (prompt: string) => projectsApi.updatePrompt(projectId, prompt),
    onSuccess: () => {
      // Invalidate project data to refetch
      queryClient.invalidateQueries({ queryKey: ['project', projectId] });
    },
  });
}

