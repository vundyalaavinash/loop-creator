const isTauri = !!(window as any).__TAURI_INTERNALS__;

export async function pickFolder(): Promise<string | null> {
  if (!isTauri) return null;
  const { open } = await import("@tauri-apps/plugin-dialog");
  const result = await open({ directory: true, multiple: false });
  return typeof result === "string" ? result : null;
}

export async function pickFiles(): Promise<string[]> {
  if (!isTauri) return [];
  const { open } = await import("@tauri-apps/plugin-dialog");
  const result = await open({ multiple: true });
  if (!result) return [];
  return Array.isArray(result) ? result : [result];
}

export { isTauri };
