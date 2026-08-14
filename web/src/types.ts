export type Division = "elementary" | "middle" | "junior" | "senior" | "custom";
export type Situation = "now" | "impossible" | "forceout";
export type Variation =
  | "no_null"
  | "symmetric_difference"
  | "multiple_operations"
  | "two_operations"
  | "union_intersection_interchangeable"
  | "universe_null_interchangeable"
  | "wild_cube"
  | "blank_card_wild"
  | "double_set"
  | "required_forbidden_card";

export interface ApiConfig {
  api_version: string;
  ruleset_id: string;
  card_order: string[];
  divisions: Division[];
  situations: Situation[];
  variations: Variation[];
  available_variations: Record<Division, Variation[]>;
  automatic_variations: Record<Division, Variation[]>;
}

export interface VariationPayload {
  active: Variation[];
  wild_cube?: string;
  wild_cube_section?: string;
  wild_cube_ordinal?: number;
  wild_as?: string;
  blank_dots: string[];
  blank_card_auto: boolean;
  double_set_expression?: string;
  double_set_uses_symmetric_difference: boolean;
  required_card?: string;
  forbidden_card?: string;
}

export interface EvaluationStep {
  expression: string;
  cards: string[];
  explanation: string;
}

export interface CheckAnswer {
  restriction: string | null;
  expression: string;
  cards: string[];
  doubled_cards: string[];
  value: number;
  restricted_universe: string[];
  violations: string[];
  steps: EvaluationStep[];
}

export interface RestrictionInterpretation {
  remaining_universe: string[];
  restrictions: Array<{
    expression: string;
    remaining_cards: string[];
    removed_cards: string[];
    link_removals: number[];
  }>;
}

export interface CheckResponse {
  api_version: string;
  ruleset_id: string;
  warnings: string[];
  answers: CheckAnswer[];
  restriction_interpretations: RestrictionInterpretation[];
}

export interface CubeUse {
  written: Record<string, number>;
  physical: Record<string, number>;
  resource_cubes: number;
  resource_inventory: Record<string, number>;
  wild_cube_used: boolean;
  wild_cube_id: string | null;
  wild_cube_as: string | null;
  notes: string[];
}

export interface SolverAnswer {
  solution: string;
  restriction: string | null;
  cards: string[];
  doubled_cards: string[];
  value: number;
  cube_count: number;
  cube_use: CubeUse;
  restriction_cube_use: CubeUse | null;
  resource_inventory: Record<string, number>;
  variation_notes: string[];
  steps: EvaluationStep[];
}

export interface SolutionGroup {
  cards: string[];
  doubled_cards: string[];
  value: number;
  answers: SolverAnswer[];
}

export interface SolveResponse {
  api_version: string;
  ruleset_id: string;
  requested: number;
  returned: number;
  search_complete: boolean;
  elapsed_seconds: number;
  warnings: string[];
  groups: SolutionGroup[];
}

export interface ApiErrorShape {
  message: string;
  issues: string[];
}
