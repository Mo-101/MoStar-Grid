/**
 * gridElements.ts — the four. Canonical. Single source.
 *
 * The dashboard bug was a rotation: names were held in one array, triads in
 * another, and they were zipped one step out of phase. ISONG ended up in the
 * fire panel; AFIM ended up standing on Mother Earth.
 *
 * The cure is structural, not a correction. Name, sigil, element, aspect and
 * triad live in ONE object. They cannot be zipped apart because they are
 * never apart.
 *
 * IDIM (River) is NOT here. Idim is river, distinct from Afim (Air).
 * If you ever find yourself adding a fifth entry, stop.
 */

import type { GlyphName } from "@/components/grid/glyph";

export interface GridElement {
  id: "ikang" | "mmong" | "afim" | "isong";
  name: string;
  sigil: string;
  element: "FIRE" | "WATER" | "AIR" | "EARTH";
  aspect: "SPIRIT" | "ESSENCE" | "MIND" | "BODY";
  triad: readonly [string, string, string];
  tint: string;
  glyph: GlyphName;
  /** Present only where the name carries weight beyond the element. */
  reverence?: string;
}

export const GRID_ELEMENTS: readonly GridElement[] = [
  {
    id: "ikang",
    name: "IKANG",
    sigil: "🜂",
    element: "FIRE",
    aspect: "SPIRIT",
    triad: ["Awakening", "Change", "Fire"],
    tint: "neon-red",
    glyph: "ban",
  },
  {
    id: "mmong",
    name: "MMỌNG", // U+1ECD. One word. Not "M MỌNG".
    sigil: "🜄",
    element: "WATER",
    aspect: "ESSENCE",
    triad: ["Pulse", "Memory", "Flow"],
    tint: "neon-cyan",
    glyph: "spark",
  },
  {
    id: "afim",
    name: "AFIM",
    sigil: "🜁",
    element: "AIR",
    aspect: "MIND",
    triad: ["Logic", "Will", "Structure"],
    tint: "neon-blue",
    glyph: "sun",
  },
  {
    id: "isong",
    name: "ISONG",
    sigil: "🜃",
    element: "EARTH",
    aspect: "BODY",
    triad: ["Form", "Action", "Creation"],
    tint: "neon-gold",
    glyph: "eye",
    reverence: "Eka Isong — Mother Earth",
  },
] as const;

export function elementById(id: GridElement["id"]): GridElement {
  const found = GRID_ELEMENTS.find((e) => e.id === id);
  if (!found) throw new Error(`Unknown grid element: ${id}`);
  return found;
}

export type ClassicalElement = "fire" | "water" | "air" | "earth";

/** Bridge for call sites that key by classical element ("fire" | "water" | ...). */
const BY_CLASSICAL = Object.fromEntries(
  GRID_ELEMENTS.map((e) => [e.element.toLowerCase(), e]),
) as Record<ClassicalElement, GridElement>;

export function elementByClassical(el: ClassicalElement): GridElement {
  const found = BY_CLASSICAL[el];
  if (!found) throw new Error(`Unknown classical element: ${el}`);
  return found;
}

/**
 * Dev guard. Import once at app boot. If someone reorders or renames, this
 * fails loudly at startup rather than silently on the front page.
 */
export function assertElementIntegrity(): void {
  const expected = [
    ["IKANG", "FIRE", "SPIRIT"],
    ["MMỌNG", "WATER", "ESSENCE"],
    ["AFIM", "AIR", "MIND"],
    ["ISONG", "EARTH", "BODY"],
  ];
  GRID_ELEMENTS.forEach((e, i) => {
    const [name, element, aspect] = expected[i];
    if (e.name !== name || e.element !== element || e.aspect !== aspect) {
      throw new Error(
        `Element integrity broken at index ${i}: expected ${name}/${element}/${aspect}, got ${e.name}/${e.element}/${e.aspect}`,
      );
    }
  });
}
