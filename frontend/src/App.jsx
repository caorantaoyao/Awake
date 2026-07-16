import { BrowserRouter as Router, Navigate, Route, Routes, useLocation } from 'react-router-dom';
import WorkspaceLayout from './layouts/WorkspaceLayout';
import Landing from './pages/Landing';
import Register from './pages/Register';
import Login from './pages/Login';
import Success from './pages/Success';
import CheckIn from './pages/CheckIn';
import Chat from './pages/Chat';
import Tasks from './pages/Tasks';
import Settings from './pages/Settings';
import Today from './pages/Today';
import Explore from './pages/Explore';
import Growth from './pages/Growth';
import Focus from './pages/Focus';

const LEGACY_CHAT_PATH = '/app/chat';
const WORKSPACE_TODAY_PATH = '/app/today';
const WORKSPACE_CHECKIN_PATH = '/app/checkin';

const LegacyChatRedirect = () => {
  const location = useLocation();
  return <Navigate to={`${LEGACY_CHAT_PATH}${location.search}`} replace />;
};

const WorkspaceTodayRedirect = () => {
  const location = useLocation();
  return <Navigate to={`${WORKSPACE_TODAY_PATH}${location.search}`} replace />;
};

const LegacyCheckInRedirect = ({ demo = false }) => {
  const location = useLocation();
  const params = new URLSearchParams(location.search);
  if (demo) params.set('demo', '1');
  const search = params.toString();
  return <Navigate to={`${WORKSPACE_CHECKIN_PATH}${search ? `?${search}` : ''}`} replace />;
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
        <Route path="/checkin" element={<LegacyCheckInRedirect />} />
        <Route path="/checkin/demo" element={<LegacyCheckInRedirect demo />} />
        <Route path="/app" element={<WorkspaceLayout />}>
          <Route index element={<WorkspaceTodayRedirect />} />
          <Route path="today" element={<Today />} />
          <Route path="chat" element={<Chat />} />
          <Route path="tasks" element={<Tasks />} />
          <Route path="focus" element={<Focus />} />
          <Route path="checkin" element={<CheckIn />} />
          <Route path="explore" element={<Explore />} />
          <Route path="growth" element={<Growth />} />
          <Route path="capabilities" element={<WorkspaceTodayRedirect />} />
          <Route path="settings" element={<Settings />} />
          <Route path="*" element={<WorkspaceTodayRedirect />} />
        </Route>
      </Routes>
    </Router>
  );
}

export default App;
