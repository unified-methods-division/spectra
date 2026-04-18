/** Labels for theme slug chips that apply the explorer `?theme=` filter. */
export function themeFilterChipLabels(
  slug: string,
  displayName?: string | null,
): { "aria-label": string; title: string } {
  const resolved =
    displayName && displayName.trim().length > 0 ? displayName.trim() : slug
  const same = resolved === slug
  if (same) {
    return {
      "aria-label": `Show only feedback tagged with theme ${slug}. Updates the theme filter and URL.`,
      title: `Filter list by theme “${slug}” — matches URL ?theme=`,
    }
  }
  return {
    "aria-label": `Show only feedback in theme ${resolved}. Theme id ${slug}. Updates the theme filter and URL.`,
    title: `Filter list by “${resolved}” — id ${slug}`,
  }
}
