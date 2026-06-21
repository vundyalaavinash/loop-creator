export interface Variant {
  prompt: string;
  output: string;
  score: number;
  reason: string;
  generation: number;
}

export interface GenerationEvent {
  generation: number;
  variants: Variant[];
  best_score: number;
  event_type: "generation" | "done";
}
