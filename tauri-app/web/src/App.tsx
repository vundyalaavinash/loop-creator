import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { LoopList } from "./pages/LoopList";
import { Builder } from "./pages/Builder";
import { Dashboard } from "./pages/Dashboard";
import { FileEditor } from "./pages/FileEditor";
import { SkillList } from "./pages/SkillList";
import { SkillBuilder } from "./pages/SkillBuilder";
import { SkillDashboard } from "./pages/SkillDashboard";
import { PromptList } from "./pages/PromptList";
import { PromptBuilder } from "./pages/PromptBuilder";
import { PromptDashboard } from "./pages/PromptDashboard";
import { PromptUse } from "./pages/PromptUse";
import { Settings } from "./pages/Settings";

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-base overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/loops" replace />} />
            <Route path="/loops" element={<LoopList />} />
            <Route path="/loops/:id/run" element={<Dashboard />} />
            <Route path="/new" element={<Builder />} />
            <Route path="/edit/:id" element={<Builder />} />
            <Route path="/files" element={<FileEditor />} />
            <Route path="/skills" element={<SkillList />} />
            <Route path="/skills/new" element={<SkillBuilder />} />
            <Route path="/skills/:name/edit" element={<SkillBuilder />} />
            <Route path="/skills/:name/run" element={<SkillDashboard />} />
            <Route path="/prompts" element={<PromptList />} />
            <Route path="/prompts/new" element={<PromptBuilder />} />
            <Route path="/prompts/:name/edit" element={<PromptBuilder />} />
            <Route path="/prompts/:name/run" element={<PromptDashboard />} />
            <Route path="/prompts/:name/use" element={<PromptUse />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
