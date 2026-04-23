/**
 * MetricLink - clickable links for metrics with deep-linking.
 *
 * INV-006: Deep-link filters preserve report context.
 */

import { Link } from "react-router"
import { cn } from "@/lib/utils"

interface MetricLinkProps {
  text: string
  sectionType: string
  rawContent: Record<string, unknown>
  periodStart: string
  periodEnd: string
}

interface LinkablePattern {
  match: string
  path: string
  filters: Record<string, string>
}

export function MetricLink({
  text,
  sectionType,
  rawContent,
  periodStart,
  periodEnd,
}: MetricLinkProps) {
  const linkablePatterns = extractLinkablePatterns(
    text,
    sectionType,
    rawContent,
  )

  if (linkablePatterns.length === 0) {
    return <span className="tabular-nums">{text}</span>
  }

  const elements: React.ReactNode[] = []
  let lastIndex = 0
  const result = text

  for (const pattern of linkablePatterns) {
    const index = result.indexOf(pattern.match, lastIndex)
    if (index === -1) continue

    if (index > lastIndex) {
      elements.push(
        <span key={`text-${lastIndex}`} className="tabular-nums">
          {result.slice(lastIndex, index)}
        </span>,
      )
    }

    const searchParams = buildEvidenceSearchParams({
      periodStart,
      periodEnd,
      filters: pattern.filters,
    })

    elements.push(
      <Link
        key={`${pattern.match}-${index}`}
        to={`${pattern.path}?${searchParams.toString()}`}
        className={cn(
          "text-primary underline underline-offset-2",
          "transition-colors duration-150 hover:text-primary/80",
          "tabular-nums",
        )}
      >
        {pattern.match}
      </Link>,
    )

    lastIndex = index + pattern.match.length
  }

  if (lastIndex < result.length) {
    elements.push(
      <span key={`text-${lastIndex}`} className="tabular-nums">
        {result.slice(lastIndex)}
      </span>,
    )
  }

  return <span>{elements}</span>
}

function extractLinkablePatterns(
  text: string,
  sectionType: string,
  rawContent: Record<string, unknown>,
): LinkablePattern[] {
  const patterns: LinkablePattern[] = []

  const themes = extractThemesFromContent(rawContent)
  for (const theme of themes) {
    if (text.includes(theme)) {
      patterns.push({
        match: theme,
        path: "/explorer",
        filters: { theme },
      })
    }
  }

  const percentMatch = text.match(/(\d+)%\s*(positive|negative|neutral)/i)
  if (percentMatch) {
    patterns.push({
      match: percentMatch[0],
      path: "/explorer",
      filters: { sentiment: percentMatch[2].toLowerCase() },
    })
  }

  if (sectionType === "recommendations") {
    const recs = (
      rawContent as { recommendations?: Array<{ id: string; title: string }> }
    ).recommendations
    if (recs) {
      for (const rec of recs) {
        if (text.includes(rec.title)) {
          patterns.push({
            match: rec.title,
            path: `/recommendations/${rec.id}`,
            filters: {},
          })
        }
      }
    }
  }

  return patterns
}

function buildEvidenceSearchParams(opts: {
  periodStart: string
  periodEnd: string
  filters: Record<string, string>
}): URLSearchParams {
  // Canonical v1 deep-linking: absolute range + stable filter keys
  // - Explorer expects `date_from` / `date_to`
  // - Include `v=1` for forward-compatible parsing
  return new URLSearchParams({
    v: "1",
    date_from: opts.periodStart,
    date_to: opts.periodEnd,
    ...opts.filters,
  })
}

function extractThemesFromContent(
  rawContent: Record<string, unknown>,
): string[] {
  const themes: string[] = []

  if (Array.isArray(rawContent.new_themes)) {
    themes.push(...(rawContent.new_themes as string[]))
  }
  if (Array.isArray(rawContent.rising_themes)) {
    themes.push(...(rawContent.rising_themes as string[]))
  }
  if (Array.isArray(rawContent.declining_themes)) {
    themes.push(...(rawContent.declining_themes as string[]))
  }
  if (Array.isArray(rawContent.improving_themes)) {
    themes.push(...(rawContent.improving_themes as string[]))
  }

  return [...new Set(themes)]
}
