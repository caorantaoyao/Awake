import { BrowserRouter as Router, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import WorkspaceLayout from './layouts/WorkspaceLayout';
import Landing from './pages/Landing';
import Register from './pages/Register';
import Login from './pages/Login';
import Success from './pages/Success';
import CheckIn from './pages/CheckIn';
import Chat from './pages/Chat';
import Tasks from './pages/Tasks';
import Capabilities from './pages/Capabilities';
import Settings from './pages/Settings';

const LEGACY_CHAT_PATH = '/app/chat';

const LegacyChatRedirect = () => {
  const location = useLocation();
  return <Navigate to={`${LEGACY_CHAT_PATH}${location.search}`} replace />;
};

const WorkspaceChatRedirect = () => {
  const location = useLocation();
  return <Navigate to={`${LEGACY_CHAT_PATH}${location.search}`} replace />;
};

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/register" element={<Register />} />
        <Route path="/login" element={<Login />} />
        <Route path="/success" element={<Success />} />
        <Route path="/chat" element={<LegacyChatRedirect />} />
        <Route path="/checkin" element={<CheckIn />} />
        <Route path="/checkin/demo" element={<CheckIn />} />
        <Route path="/app" element={<WorkspaceLayout />}>
          <Route index element={<WorkspaceChatRedirect />} />
          <Route path="chat" element={<Chat />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="capabilities" element={<Capabilities />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<WorkspaceChatRedirect />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
