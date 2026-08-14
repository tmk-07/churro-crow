import type { CheckAnswer } from "./types";

export function cardsText(cards: string[], doubledCards: string[] = []): string {
  if (!cards.length) return "no cards";
  const doubled = new Set(doubledCards);
  return cards.map((card) => doubled.has(card) ? `${card} (2)` : card).join(" · ");
}

export function inventoryText(inventory: Record<string, number>): string {
  const entries = Object.entries(inventory);
  if (!entries.length) return "none";
  return entries.map(([symbol, count]) => count === 1 ? symbol : `${symbol}×${count}`).join("  ");
}

export function answersByValue(answers: CheckAnswer[]): Map<number, CheckAnswer[]> {
  const groups = new Map<number, CheckAnswer[]>();
  for (const answer of answers) {
    groups.set(answer.value, [...(groups.get(answer.value) ?? []), answer]);
  }
  return new Map([...groups.entries()].sort(([left], [right]) => left - right));
}

export function cubeOccurrences(sections: Record<string, string>) {
  const normalize: Record<string, string> = {
    "U": "u", "∪": "u", "∩": "n", "⊂": "c", "−": "-", "’": "'", "′": "'",
    "b": "B", "r": "R", "g": "G", "y": "Y", "v": "V", "z": "Z", "N": "n", "C": "c",
  };
  const allowed = new Set("BRGYVZun-'c=".split(""));
  const output: Array<{ section: string; symbol: string; ordinal: number }> = [];
  for (const [section, text] of Object.entries(sections)) {
    const counts: Record<string, number> = {};
    for (const raw of text.replaceAll(/\s/g, "")) {
      const symbol = normalize[raw] ?? raw;
      if (!allowed.has(symbol)) continue;
      counts[symbol] = (counts[symbol] ?? 0) + 1;
      output.push({ section, symbol, ordinal: counts[symbol] });
    }
  }
  return output;
}
