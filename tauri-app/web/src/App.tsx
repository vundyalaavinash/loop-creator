import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { LoopList } from "./pages/LoopList";
import { Builder } from "./pages/Builder";
import { Dashboard } from "./pages/Dashboard";
import { FileEditor } from "./pages/FileEditor";

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
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
