import { Routes, Route } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import Overview from './pages/Overview';
import AnalyzeDiscussion from './pages/AnalyzeDiscussion';
import Decisions from './pages/Decisions';
import DecisionDetail from './pages/DecisionDetail';
import ADRLibrary from './pages/ADRLibrary';
import SearchPage from './pages/Search';
import PRRadar from './pages/PRRadar';
import SettingsPage from './pages/Settings';

export default function App() {
  return (
    <div className="flex min-h-screen">
      <Sidebar />

      {/* Main content area — offset for sidebar */}
      <main className="ml-60 flex-1 px-8 py-8">
        <div className="mx-auto max-w-5xl">
          <Routes>
            <Route path="/" element={<Overview />} />
            <Route path="/analyze" element={<AnalyzeDiscussion />} />
            <Route path="/decisions" element={<Decisions />} />
            <Route path="/decisions/:id" element={<DecisionDetail />} />
            <Route path="/adrs" element={<ADRLibrary />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/radar" element={<PRRadar />} />
            <Route path="/settings" element={<SettingsPage />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}
