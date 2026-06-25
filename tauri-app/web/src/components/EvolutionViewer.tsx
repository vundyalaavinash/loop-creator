import { useState } from "react";
import { GenerationEvent, Variant } from "../types";
import { ScoreBar } from "./ScoreBar";

interface Props {
  events: GenerationEvent[];
  isRunning: boolean;
}

function scoreColor(score: number) {
  if (score >= 0.75) return "#01C7B1";
  if (score >= 0.45) return "#F59E0B";
  return "#6B7280";
}

function VariantCard({ v, rank, prevScore }: { v: Variant; rank: number; prevScore?: number }) {
  const [expanded, setExpanded] = useState(false);
  const col = scoreColor(v.score);
  return (
    <div
      style={{
        border: `1px solid ${col}30`,
        borderRadius: 6,
        background: "#0A0A0A",
        marginBottom: 8,
        overflow: "hidden",
      }}
    >
      {/* Header row */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "8px 12px",
          cursor: "pointer",
          userSelect: "none",
        }}
        onClick={() => setExpanded((p) => !p)}
      >
        <span
          style={{
            fontSize: 10,
            fontFamily: "monospace",
            color: "#6B7280",
            minWidth: 18,
          }}
        >
          #{rank}
        </span>
        <div style={{ flex: 1 }}>
          <ScoreBar label="" score={v.score} prevScore={prevScore} />
        </div>
        <span
          style={{
            fontSize: 11,
            fontFamily: "monospace",
            color: col,
            minWidth: 36,
            textAlign: "right",
          }}
        >
          {(v.score * 100).toFixed(0)}%
        </span>
        <span
          style={{
            fontSize: 10,
            fontFamily: "monospace",
            color: "#6B7280",
            marginLeft: 4,
          }}
        >
          {expanded ? "▲" : "▼"}
        </span>
      </div>

      {/* Reason always visible */}
      <div
        style={{
          padding: "0 12px 6px",
          fontSize: 11,
          fontFamily: "monospace",
          color: "#6B7280",
          fontStyle: "italic",
          lineHeight: 1.5,
        }}
      >
        {v.reason}
      </div>

      {/* Expanded: show output and prompt */}
      {expanded && (
        <div style={{ borderTop: "1px solid #1E1E1E" }}>
          <div style={{ padding: "10px 12px" }}>
            <div
              style={{
                fontSize: 10,
                fontFamily: "monospace",
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: 1,
                marginBottom: 6,
              }}
            >
              Output
            </div>
            <pre
              style={{
                fontSize: 12,
                fontFamily: "monospace",
                color: "#FFFFFF",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                margin: 0,
                maxHeight: 300,
                overflowY: "auto",
                lineHeight: 1.6,
              }}
            >
              {v.output}
            </pre>
          </div>
          <div
            style={{
              padding: "8px 12px 10px",
              borderTop: "1px solid #1E1E1E",
            }}
          >
            <div
              style={{
                fontSize: 10,
                fontFamily: "monospace",
                color: "#6B7280",
                textTransform: "uppercase",
                letterSpacing: 1,
                marginBottom: 6,
              }}
            >
              Prompt used
            </div>
            <pre
              style={{
                fontSize: 11,
                fontFamily: "monospace",
                color: "#9B6DFF",
                whiteSpace: "pre-wrap",
                wordBreak: "break-word",
                margin: 0,
                maxHeight: 200,
                overflowY: "auto",
                lineHeight: 1.5,
              }}
            >
              {v.prompt}
            </pre>
          </div>
        </div>
      )}
    </div>
  );
}

function GenBlock({
  gen,
  variants,
  live,
  prevBest,
}: {
  gen: number;
  variants: Variant[];
  live: boolean;
  prevBest?: number;
}) {
  const sorted = [...variants].sort((a, b) => b.score - a.score);
  const best = sorted[0]?.score ?? 0;

  return (
    <div
      style={{
        border: live ? "1px solid #01C7B130" : "1px solid #1E1E1E",
        borderRadius: 8,
        background: "#111111",
        padding: "12px 14px",
        marginBottom: 10,
        opacity: live ? 0.85 : 1,
      }}
    >
      {/* Gen header */}
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 10,
        }}
      >
        <span
          style={{
            fontSize: 12,
            fontFamily: "monospace",
            color: "#FFFFFF",
            fontWeight: 600,
          }}
        >
          Generation {gen}
        </span>
        {live && (
          <span
            style={{
              fontSize: 11,
              fontFamily: "monospace",
              color: "#01C7B1",
              animation: "pulse 1.5s infinite",
            }}
          >
            · computing
          </span>
        )}
        <span
          style={{
            marginLeft: "auto",
            fontSize: 11,
            fontFamily: "monospace",
            color: scoreColor(best),
          }}
        >
          {variants.length} variant{variants.length !== 1 ? "s" : ""}
          {" · "}
          best {(best * 100).toFixed(0)}%
          {!live && prevBest !== undefined && best > prevBest && (
            <span style={{ color: "#01C7B1", marginLeft: 6 }}>
              ↑ +{((best - prevBest) * 100).toFixed(0)}
            </span>
          )}
          {!live && prevBest !== undefined && best < prevBest && (
            <span style={{ color: "#6B7280", marginLeft: 6 }}>
              ↓ {((best - prevBest) * 100).toFixed(0)}
            </span>
          )}
        </span>
      </div>

      {/* All variants */}
      {sorted.map((v, i) => (
        <VariantCard
          key={`${gen}-${i}`}
          v={v}
          rank={i + 1}
          prevScore={i === 0 ? prevBest : undefined}
        />
      ))}
    </div>
  );
}

export function EvolutionViewer({ events, isRunning }: Props) {
  const genEvents = events.filter((e) => e.event_type === "generation");
  const progressEvents = events.filter((e) => e.event_type === "progress");

  const completedGens = new Set(genEvents.map((e) => e.generation));

  // Accumulate all variants per live generation
  const liveVariants: Record<number, Variant[]> = {};
  for (const ev of progressEvents) {
    if (!completedGens.has(ev.generation)) {
      (liveVariants[ev.generation] ??= []).push(...ev.variants);
    }
  }

  const hasContent = genEvents.length > 0 || Object.keys(liveVariants).length > 0;
  if (!hasContent && !isRunning) return null;

  // Build best score per completed gen for delta display
  const genBests = genEvents.map((e) => Math.max(...e.variants.map((v) => v.score)));

  return (
    <div
      style={{
        background: "#0A0A0A",
        border: "1px solid #1E1E1E",
        borderRadius: 8,
        padding: "16px 18px",
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 8,
          marginBottom: 14,
        }}
      >
        <h2
          style={{
            color: "#FFFFFF",
            fontFamily: "sans-serif",
            fontWeight: 600,
            fontSize: 15,
            margin: 0,
          }}
        >
          Evolution Progress
        </h2>
        {isRunning && (
          <span
            style={{
              fontSize: 13,
              fontFamily: "monospace",
              color: "#01C7B1",
            }}
          >
            · running
          </span>
        )}
        {genEvents.length > 0 && (
          <span
            style={{
              marginLeft: "auto",
              fontSize: 11,
              fontFamily: "monospace",
              color: "#6B7280",
            }}
          >
            {genEvents.length} gen{genEvents.length !== 1 ? "s" : ""} complete
          </span>
        )}
      </div>

      {genEvents.map((ev, idx) => (
        <GenBlock
          key={`gen-${ev.generation}`}
          gen={ev.generation}
          variants={ev.variants}
          live={false}
          prevBest={idx > 0 ? genBests[idx - 1] : undefined}
        />
      ))}

      {Object.entries(liveVariants).map(([genStr, variants]) => (
        <GenBlock
          key={`live-${genStr}`}
          gen={Number(genStr)}
          variants={variants}
          live={true}
          prevBest={genBests[genBests.length - 1]}
        />
      ))}

      {isRunning && !hasContent && (
        <div
          style={{
            fontSize: 12,
            fontFamily: "monospace",
            color: "#6B7280",
            padding: "8px 0",
          }}
        >
          Starting evolution…
        </div>
      )}
    </div>
  );
}
