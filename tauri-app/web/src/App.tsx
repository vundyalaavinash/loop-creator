import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { Sidebar } from "./components/Sidebar";
import { LoopList } from "./pages/LoopList";
import { Builder } from "./pages/Builder";

// Pages imported lazily — stubs until Tasks 12-13 implement them
const Placeholder = ({ name }: { name: string }) => (
  <div className="flex-1 p-8 text-muted font-mono">{name} — coming soon</div>
);

export default function App() {
  return (
    <BrowserRouter>
      <div className="flex h-screen bg-base overflow-hidden">
        <Sidebar />
        <main className="flex-1 overflow-y-auto">
          <Routes>
            <Route path="/" element={<Navigate to="/loops" replace />} />
            <Route path="/loops" element={<LoopList />} />
            <Route path="/loops/:id/run" element={<Placeholder name="Dashboard" />} />
            <Route path="/new" element={<Builder />} />
            <Route path="/edit/:id" element={<Builder />} />
            <Route path="/files" element={<Placeholder name="FileEditor" />} />
          </Routes>
        </main>
      </div>
    </BrowserRouter>
  );
}
