// Project types
export interface Project {
  project_id: string;
  title: string;
  description: string;
  date: string;
  tags: string[];
}

// Paper types
export interface Paper {
  hash: string;
  title: string;
  description: string;
  link?: string;
  authors?: string;
  publication_date?: string;
  venue_name?: string;
  venue_type?: string;
  is_oa?: boolean;
  oa_status?: string;
  pdf_url?: string;
  oa_url?: string;
  cited_by_count?: number;
  fwci?: number;
  citation_normalized_percentile?: {
    value: number;
    is_in_top_1_percent?: boolean;
    is_in_top_10_percent?: boolean;
  };
  rating?: number;
  is_replacement?: boolean;
}

// API Response types
export interface ApiResponse<T> {
  success?: boolean;
  error?: string;
  data?: T;
}

export interface RecommendationsResponse {
  recommendations?: Paper[];
  thought?: string;
  out_of_scope?: {
    message: {
      short_explanation: string;
      explanation: string;
      suggestion: string;
    };
  };
  no_results?: {
    message: {
      explanation: string;
      filter_criteria?: Record<string, { op: string; value: any }>;
      closest_values?: Record<string, { value: any; direction: string }>;
    };
  };
  error?: string;
}

