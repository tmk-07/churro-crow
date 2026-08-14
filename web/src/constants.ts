import type { ApiConfig, Division, Situation, Variation, VariationPayload } from "./types";

export const CARD_ORDER = [
  "BR", "BRY", "BY", "B",
  "BRG", "BRGY", "BGY", "BG",
  "RG", "RGY", "GY", "G",
  "R", "RY", "Y", "blank",
];

export const DIVISION_LABELS: Record<Division, string> = {
  elementary: "Elementary",
  middle: "Middle",
  junior: "Junior",
  senior: "Senior",
  custom: "Custom practice",
};

export const SITUATION_LABELS: Record<Situation, string> = {
  now: "Now",
  impossible: "Impossible",
  forceout: "Forceout",
};

export const SITUATION_HELP: Record<Situation, string> = {
  now: "At most one Resource cube may be used.",
  impossible: "Any actual Resource cubes may be used.",
  forceout: "No Resource cubes remain.",
};

export const VARIATION_LABELS: Record<Variation, string> = {
  no_null: "No Null Restrictions",
  symmetric_difference: "Symmetric Difference",
  multiple_operations: "Multiple Operations",
  two_operations: "Two Operations",
  union_intersection_interchangeable: "U and ∩ Interchangeable",
  universe_null_interchangeable: "V and Z Interchangeable",
  wild_cube: "Wild Cube",
  blank_card_wild: "Blank Card Wild",
  double_set: "Double Set",
  required_forbidden_card: "Required/Forbidden Card",
};

export const DEFAULT_VARIATIONS: VariationPayload = {
  active: [],
  blank_dots: [],
  blank_card_auto: false,
  double_set_uses_symmetric_difference: false,
};

const allVariations = Object.keys(VARIATION_LABELS) as Variation[];
const automatic: Record<Division, Variation[]> = {
  elementary: [],
  middle: [],
  junior: ["multiple_operations", "union_intersection_interchangeable", "universe_null_interchangeable"],
  senior: ["multiple_operations", "union_intersection_interchangeable", "universe_null_interchangeable"],
  custom: [],
};

export const FALLBACK_CONFIG: ApiConfig = {
  api_version: "v1",
  ruleset_id: "agloa-2026-27",
  card_order: CARD_ORDER,
  divisions: ["elementary", "middle", "junior", "senior", "custom"],
  situations: ["now", "impossible", "forceout"],
  variations: allVariations,
  available_variations: {
    elementary: ["wild_cube", "union_intersection_interchangeable", "universe_null_interchangeable", "two_operations", "multiple_operations"],
    middle: ["wild_cube", "union_intersection_interchangeable", "universe_null_interchangeable", "two_operations", "multiple_operations", "no_null"],
    junior: ["wild_cube", "two_operations", "no_null", "double_set", "required_forbidden_card", "blank_card_wild"],
    senior: ["wild_cube", "two_operations", "no_null", "double_set", "required_forbidden_card", "blank_card_wild", "symmetric_difference"],
    custom: allVariations,
  },
  automatic_variations: automatic,
};
