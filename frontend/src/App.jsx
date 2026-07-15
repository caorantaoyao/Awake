import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Landing from './pages/Landing';
import Register from './pages/Register';
import Success from './pages/Success';
import CheckIn from './pages/CheckIn';
import Chat from './pages/Chat';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/register" element={<Register />} />
        <Route path="/success" element={<Success />} />
        <Route path="/chat" element={<Chat />} />
        <Route path="/checkin" element={<CheckIn />} />
        <Route path="/checkin/demo" element={<CheckIn />} />
      </Routes>
    </Router>
  );
}

export default App;
