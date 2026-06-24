export interface Variant {
  prompt: string;
  output: string;
  score: number;       // 0.0 – 1.0
  reason: string;
  generation: number;
}

export interface GenerationEvent {
  event_type: "generation" | "done" | "error";
  generation: number;
  variants: Variant[];
  best_score: number;
}

export interface LoopSummary {
  id: string;
  name: string;
  loop_type: string;
  last_modified: number;   // epoch seconds
  best_score: number | null;
  active: boolean;
}

export interface FileNode {
  name: string;
  path: string;
  is_dir: boolean;
  children?: FileNode[];
}

export interface LoopSpec {
  id: string;
  type: string;
  task: string;
  goal: string;
  generator: { cli: string; model: string };
  judge: { cli: string; rubric: string; model: string };
  context: {
    project: boolean;
    history: boolean;
    external: string[];
    mcp_auto_discover: boolean;
    project_root: string;
  };
  gepa: {
    population_size: number;
    top_k: number;
    max_generations: number;
    fitness_threshold: number;
    stagnation_limit: number;
  };
}

export function getBaseUrl(): string {
  const port = (window as any).__LC_PORT__ ?? 5001;
  return `http://localhost:${port}`;
}

export interface SkillSummary {
  name: string;
  category: string;
  last_modified: number;
}

export interface SkillSpec {
  name: string;
  description_goal: string;
  category: string;
  target_platforms: string[];
  generator: { cli: string; model: string };
  judge: { cli: string; rubric: string; model: string };
  gepa: { population_size: number; max_generations: number; fitness_threshold: number };
}

export interface PromptSummary {
  name: string;
  description_goal: string;
  last_modified: number;
}

export interface PromptSpec {
  name: string;
  description_goal: string;
  variables: string[];
  generator: { cli: string; model: string };
  judge: { cli: string; rubric: string; model: string };
  gepa: { population_size: number; max_generations: number; fitness_threshold: number };
}

export interface AppConfig {
  whisper_backend: string;
  whisper_model: string;
  openai_api_key: string;
}
