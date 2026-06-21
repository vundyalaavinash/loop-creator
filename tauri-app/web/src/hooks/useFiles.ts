import { useState, useCallback } from "react";
import { FileNode, getBaseUrl } from "../types";

export function useFiles() {
  const [files, setFiles] = useState<FileNode[]>([]);
  const [content, setContent] = useState<string>("");
  const [error, setError] = useState<string | null>(null);

  const listFiles = useCallback(async (path: string) => {
    const r = await fetch(
      `${getBaseUrl()}/api/files?path=${encodeURIComponent(path)}`
    );
    if (!r.ok) { setError(`Failed to list files: ${r.status}`); return []; }
    const data: FileNode[] = await r.json();
    setFiles(data);
    return data;
  }, []);

  const readFile = useCallback(async (path: string) => {
    const r = await fetch(
      `${getBaseUrl()}/api/files/content?path=${encodeURIComponent(path)}`
    );
    if (!r.ok) { setError(`Failed to read file: ${r.status}`); return ""; }
    const data = await r.json();
    setContent(data.content);
    return data.content as string;
  }, []);

  const writeFile = useCallback(async (path: string, text: string) => {
    setError(null);
    const r = await fetch(`${getBaseUrl()}/api/files/content`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ path, content: text }),
    });
    if (!r.ok) setError("Save failed");
    return r.ok;
  }, []);

  return { files, content, error, listFiles, readFile, writeFile, setContent };
}
