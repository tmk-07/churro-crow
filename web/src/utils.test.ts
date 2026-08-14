import { describe, expect, it } from "vitest";
import { answersByValue, cardsText, cubeOccurrences } from "./utils";

describe("presentation helpers", () => {
  it("marks Double Set cards without duplicating them", () => {
    expect(cardsText(["BR", "GY", "RY"], ["BR", "RY"]))
      .toBe("BR (2) · GY · RY (2)");
  });

  it("groups checker interpretations by ascending value", () => {
    const sample = (value: number) => ({ value } as never);
    expect([...answersByValue([sample(10), sample(6), sample(10)]).keys()])
      .toEqual([6, 10]);
  });

  it("identifies a specific physical wild cube occurrence", () => {
    expect(cubeOccurrences({ required: "rr-u", resources: "r" }))
      .toEqual([
        { section: "required", symbol: "R", ordinal: 1 },
        { section: "required", symbol: "R", ordinal: 2 },
        { section: "required", symbol: "-", ordinal: 1 },
        { section: "required", symbol: "u", ordinal: 1 },
        { section: "resources", symbol: "R", ordinal: 1 },
      ]);
  });
});
