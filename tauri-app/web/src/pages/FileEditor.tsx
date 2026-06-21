import { useState, useEffect } from "react";
import MonacoEditor from "@monaco-editor/react";
import { useFiles } from "../hooks/useFiles";
import { FileNode } from "../types";

function getLanguage(path: string): string {
  const ext = path.split(".").pop() ?? "";
  const map: Record<string, string> = {
    py: "python", ts: "typescript", tsx: "typescript",
    js: "javascript", jsx: "javascript", md: "markdown",
    json: "json", yaml: "yaml", yml: "yaml", sh: "shell",
    rs: "rust", toml: "toml",
  };
  return map[ext] ?? "plaintext";
}

function FileTree({ nodes, onSelect }: { nodes: FileNode[]; onSelect: (n: FileNode) => void }) {
  return (
    <ul className="space-y-0.5">
      {nodes.map((n) => (
        <li key={n.path}>
          <button
            onClick={() => !n.is_dir && onSelect(n)}
            className={`w-full text-left px-3 py-1 text-xs font-mono rounded transition-colors ${
              n.is_dir
                ? "text-accent-purple hover:bg-elevated cursor-default"
                : "text-muted hover:text-primary hover:bg-elevated"
            }`}
          >
            {n.is_dir ? "▸ " : "  "}{n.name}
          </button>
        </li>
      ))}
    </ul>
  );
}

export function FileEditor() {
  const { files, content, error, listFiles, readFile, writeFile, setContent } = useFiles();
  const [dirPath, setDirPath] = useState("");
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [dirty, setDirty] = useState(false);
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    listFiles(dirPath);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function openDir() {
    await listFiles(dirPath);
  }

  async function openFile(node: FileNode) {
    setSelectedPath(node.path);
    await readFile(node.path);
    setDirty(false);
  }

  async function save() {
    if (!selectedPath) return;
    setSaving(true);
    await writeFile(selectedPath, content);
    setSaving(false);
    setDirty(false);
  }

  return (
    <div className="flex h-full">
      {/* Left: file tree */}
      <div className="w-56 bg-surface border-r border-border-color flex flex-col flex-shrink-0">
        <div className="p-3 border-b border-border-color">
          <input
            className="w-full bg-elevated border border-border-color rounded px-2 py-1 text-xs font-mono text-primary focus:outline-none focus:border-accent-teal"
            value={dirPath}
            onChange={(e) => setDirPath(e.target.value)}
            placeholder="Enter path…"
            onKeyDown={(e) => e.key === "Enter" && openDir()}
          />
        </div>
        <div className="flex-1 overflow-y-auto py-2">
          <FileTree nodes={files} onSelect={openFile} />
        </div>
      </div>

      {/* Right: editor */}
      <div className="flex-1 flex flex-col">
        {selectedPath && (
          <div className="flex items-center justify-between px-4 py-2 border-b border-border-color bg-surface">
            <span className="text-xs font-mono text-muted">
              {selectedPath}
              {dirty && <span className="ml-2 text-accent-purple">●</span>}
            </span>
            <button
              onClick={save}
              disabled={saving || !dirty}
              className="text-xs font-mono px-3 py-1 bg-accent-teal text-base rounded disabled:opacity-40 hover:opacity-90 transition-opacity"
            >
              {saving ? "Saving…" : "Save"}
            </button>
          </div>
        )}
        {error && (
          <div className="px-4 py-2 text-xs text-red-400 font-mono bg-red-950">{error}</div>
        )}
        <div className="flex-1">
          <MonacoEditor
            height="100%"
            language={getLanguage(selectedPath ?? "")}
            value={content}
            onChange={(val) => { setContent(val ?? ""); setDirty(true); }}
            theme="vs-dark"
            options={{
              fontFamily: "JetBrains Mono",
              fontSize: 13,
              minimap: { enabled: false },
              padding: { top: 12 },
              scrollBeyondLastLine: false,
            }}
          />
        </div>
      </div>
    </div>
  );
}
