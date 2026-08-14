import { VARIATION_LABELS } from "../constants";
import type { ApiConfig, Division, Variation, VariationPayload } from "../types";
import { cubeOccurrences } from "../utils";

interface VariationPanelProps {
  config: ApiConfig;
  division: Division;
  universe: string[];
  value: VariationPayload;
  onChange: (value: VariationPayload) => void;
  cubeSections?: Record<string, string>;
  checker?: boolean;
}

const checkerHidden = new Set<Variation>([
  "wild_cube",
  "multiple_operations",
  "union_intersection_interchangeable",
  "universe_null_interchangeable",
]);

export function VariationPanel({
  config,
  division,
  universe,
  value,
  onChange,
  cubeSections = {},
  checker = false,
}: VariationPanelProps) {
  const automatic = new Set(config.automatic_variations[division]);
  const available = new Set([
    ...config.available_variations[division],
    ...config.automatic_variations[division],
  ]);
  const options = config.variations.filter((variation) =>
    available.has(variation) && !(checker && checkerHidden.has(variation))
  );
  const active = new Set([...value.active, ...automatic]);
  const wildOptions = cubeOccurrences(cubeSections);

  const toggle = (variation: Variation) => {
    if (automatic.has(variation)) return;
    const next = new Set(value.active);
    if (next.has(variation)) next.delete(variation);
    else next.add(variation);
    onChange({ ...value, active: [...next] });
  };

  const patch = (next: Partial<VariationPayload>) => onChange({ ...value, ...next });

  return (
    <details className="variation-panel">
      <summary>
        <span>Variations</span>
        <span className="summary-meta">{active.size} active</span>
      </summary>
      <div className="variation-body">
        <p className="muted">Automatic division rules are locked on. Other declarations can be reviewed before proceeding.</p>
        <div className="variation-grid">
          {options.map((variation) => (
            <label className={`check-tile${automatic.has(variation) ? " automatic" : ""}`} key={variation}>
              <input
                type="checkbox"
                checked={active.has(variation)}
                disabled={automatic.has(variation)}
                onChange={() => toggle(variation)}
              />
              <span>{VARIATION_LABELS[variation]}</span>
              {automatic.has(variation) && <small>automatic</small>}
            </label>
          ))}
        </div>

        {active.has("wild_cube") && (
          <div className="subfields three-up">
            <label>
              <span>Physical wild cube</span>
              <select
                value={value.wild_cube ? `${value.wild_cube_section}:${value.wild_cube}:${value.wild_cube_ordinal ?? 1}` : ""}
                onChange={(event) => {
                  const [section, symbol, ordinal] = event.target.value.split(":");
                  patch(event.target.value ? {
                    wild_cube_section: section,
                    wild_cube: symbol,
                    wild_cube_ordinal: Number(ordinal),
                  } : { wild_cube_section: undefined, wild_cube: undefined, wild_cube_ordinal: undefined });
                }}
              >
                <option value="">Choose a cube</option>
                {wildOptions.map((option) => (
                  <option
                    key={`${option.section}:${option.symbol}:${option.ordinal}`}
                    value={`${option.section}:${option.symbol}:${option.ordinal}`}
                  >
                    {option.section} · {option.symbol} #{option.ordinal}
                  </option>
                ))}
              </select>
            </label>
            <label>
              <span>Wild interpretation</span>
              <select value={value.wild_as ?? ""} onChange={(event) => patch({ wild_as: event.target.value || undefined })}>
                <option value="">Let solver choose</option>
                {["B", "R", "G", "Y", "V", "Z", "u", "n", "-", "'"].map((symbol) => (
                  <option key={symbol} value={symbol}>{symbol}</option>
                ))}
              </select>
            </label>
          </div>
        )}

        {active.has("blank_card_wild") && (
          <div className="subfields">
            {!checker && (
              <label className="inline-check">
                <input type="checkbox" checked={value.blank_card_auto} onChange={(event) => patch({ blank_card_auto: event.target.checked })} />
                Let the solver choose the blank card colors
              </label>
            )}
            {(checker || !value.blank_card_auto) && (
              <fieldset>
                <legend>Colors placed on blank</legend>
                <div className="compact-checks">
                  {["B", "R", "G", "Y"].map((color) => (
                    <label key={color}>
                      <input
                        type="checkbox"
                        checked={value.blank_dots.includes(color)}
                        onChange={() => patch({
                          blank_dots: value.blank_dots.includes(color)
                            ? value.blank_dots.filter((item) => item !== color)
                            : [...value.blank_dots, color],
                        })}
                      />
                      {color}
                    </label>
                  ))}
                </div>
              </fieldset>
            )}
          </div>
        )}

        {active.has("double_set") && (
          <div className="subfields two-up">
            <label>
              <span>Set that counts double</span>
              <input
                value={value.double_set_expression ?? ""}
                placeholder="B U (R')"
                onChange={(event) => patch({ double_set_expression: event.target.value || undefined })}
              />
            </label>
            {active.has("symmetric_difference") && (
              <label className="inline-check bottom-align">
                <input
                  type="checkbox"
                  checked={value.double_set_uses_symmetric_difference}
                  onChange={(event) => patch({ double_set_uses_symmetric_difference: event.target.checked })}
                />
                Symmetric Difference was selected first
              </label>
            )}
          </div>
        )}

        {active.has("required_forbidden_card") && (
          <div className="subfields two-up">
            <label>
              <span>Required card</span>
              <select value={value.required_card ?? ""} onChange={(event) => patch({ required_card: event.target.value || undefined })}>
                <option value="">None</option>
                {universe.map((card) => <option key={card}>{card}</option>)}
              </select>
            </label>
            <label>
              <span>Forbidden card</span>
              <select value={value.forbidden_card ?? ""} onChange={(event) => patch({ forbidden_card: event.target.value || undefined })}>
                <option value="">None</option>
                {universe.map((card) => <option key={card}>{card}</option>)}
              </select>
            </label>
          </div>
        )}
      </div>
    </details>
  );
}
