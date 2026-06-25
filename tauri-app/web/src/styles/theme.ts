// Shared design tokens — single source of truth for all pages
export const C = {
  bg:       "#000000",
  surface:  "#0A0A0A",
  elevated: "#111111",
  border:   "#1E1E1E",
  text:     "#FFFFFF",
  muted:    "#6B7280",
  teal:     "#01C7B1",
  purple:   "#9B6DFF",
  red:      "#FF6B6B",
  redDark:  "#7F1D1D",
} as const;

export const S = {
  // Layout
  page:    { padding: 24 } as React.CSSProperties,
  section: { background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: 16, marginBottom: 16 } as React.CSSProperties,
  card:    { background: C.surface, border: `1px solid ${C.border}`, borderRadius: 8, padding: "12px 16px", marginBottom: 8, display: "flex", alignItems: "center", gap: 12 } as React.CSSProperties,

  // Typography
  pageTitle: { color: C.text, fontFamily: "sans-serif", fontWeight: 600, fontSize: 18, margin: 0 } as React.CSSProperties,
  subtitle:  { color: C.muted, fontFamily: "monospace", fontSize: 12 } as React.CSSProperties,
  label:     { display: "block", color: C.muted, marginBottom: 4, fontSize: 12, fontFamily: "monospace", textTransform: "uppercase", letterSpacing: 1 } as React.CSSProperties,

  // Form inputs
  input:    { width: "100%", background: C.elevated, border: `1px solid ${C.border}`, borderRadius: 6, color: C.text, padding: "8px 12px", fontSize: 14, fontFamily: "monospace", boxSizing: "border-box" } as React.CSSProperties,
  textarea: { width: "100%", background: C.elevated, border: `1px solid ${C.border}`, borderRadius: 6, color: C.text, padding: "8px 12px", fontSize: 14, fontFamily: "monospace", resize: "vertical", boxSizing: "border-box" } as React.CSSProperties,
  select:   { width: "100%", maxWidth: 320, background: C.elevated, border: `1px solid ${C.border}`, borderRadius: 6, color: C.text, padding: "8px 12px", fontSize: 14, fontFamily: "monospace" } as React.CSSProperties,

  // Buttons
  btnPrimary:   { background: C.teal,    color: C.bg,    border: "none",                         borderRadius: 6, padding: "9px 22px", fontWeight: 700, cursor: "pointer", fontSize: 13, fontFamily: "monospace" } as React.CSSProperties,
  btnSecondary: { background: C.elevated, color: C.text, border: `1px solid ${C.border}`,        borderRadius: 6, padding: "9px 22px", fontWeight: 600, cursor: "pointer", fontSize: 13, fontFamily: "monospace" } as React.CSSProperties,
  btnStop:      { background: C.redDark, color: C.red,   border: `1px solid ${C.redDark}`,       borderRadius: 6, padding: "9px 22px", fontWeight: 700, cursor: "pointer", fontSize: 13, fontFamily: "monospace" } as React.CSSProperties,
  btnBrowse:    { background: "transparent", color: C.teal, border: `1px solid ${C.border}`,     borderRadius: 6, padding: "6px 14px", cursor: "pointer", fontSize: 12, fontFamily: "monospace", whiteSpace: "nowrap" } as React.CSSProperties,

  // Row action buttons
  btnRun:  { fontSize: 12, fontFamily: "monospace", padding: "4px 12px", border: `1px solid ${C.teal}`,   color: C.teal,   background: "transparent", borderRadius: 4, cursor: "pointer" } as React.CSSProperties,
  btnEdit: { fontSize: 12, fontFamily: "monospace", padding: "4px 12px", border: `1px solid ${C.border}`, color: C.muted,  background: "transparent", borderRadius: 4, cursor: "pointer" } as React.CSSProperties,
  btnUse:  { fontSize: 12, fontFamily: "monospace", padding: "4px 12px", border: `1px solid ${C.purple}`, color: C.purple, background: "transparent", borderRadius: 4, cursor: "pointer" } as React.CSSProperties,
  btnDel:  { fontSize: 12, fontFamily: "monospace", padding: "4px 12px", border: `1px solid ${C.redDark}`, color: C.red,   background: "transparent", borderRadius: 4, cursor: "pointer" } as React.CSSProperties,

  // Builder chip (active/inactive)
  chip: (active: boolean): React.CSSProperties => ({
    padding: "6px 14px", borderRadius: 6,
    border: `1px solid ${active ? C.teal : C.border}`,
    color: active ? C.teal : C.muted,
    background: active ? C.elevated : "transparent",
    cursor: "pointer", fontSize: 12, fontFamily: "monospace",
  }),

  // Small badge/tag
  tag: (color: string): React.CSSProperties => ({
    fontSize: 11, fontFamily: "monospace", padding: "2px 8px",
    background: C.elevated, border: `1px solid ${color}40`,
    color, borderRadius: 4, whiteSpace: "nowrap",
  }),

  // Feedback banners
  errorBanner: { marginBottom: 16, padding: 12, background: "#1A0505", border: `1px solid ${C.redDark}`, color: C.red, borderRadius: 6, fontFamily: "monospace", fontSize: 13 } as React.CSSProperties,
} as const;
