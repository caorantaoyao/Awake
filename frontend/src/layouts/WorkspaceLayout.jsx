import { useCallback, useEffect, useMemo, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import ContextBar from '../components/ContextBar';
import Sidebar from '../components/Sidebar';
import { getStoredStudent } from '../api/client';

const createStudentDeerflowStatus = () => ({
  availability: 'private',
  online: null,
  label: '按需连接',
  model: null,
  assistant_id: null,
  error: null
});

const safeGetStoredStudent = () => {
  try {
    return getStoredStudent();
  } catch {
    return null;
  }
};

const getStudentSnapshot = () => safeGetStoredStudent();

const WorkspaceLayout = () => {
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [student, setStudent] = useState(getStudentSnapshot);
  const [deerflowStatus, setDeerflowStatus] = useState(createStudentDeerflowStatus);
  const currentModel = deerflowStatus.model;

  const refreshDeerflowStatus = useCallback(async () => {
    const nextStatus = createStudentDeerflowStatus();
    setDeerflowStatus(nextStatus);
    return nextStatus;
  }, []);

  const outletContext = useMemo(
    () => ({
      student,
      setStudent,
      deerflowStatus,
      currentModel,
      refreshDeerflowStatus
    }),
    [currentModel, deerflowStatus, refreshDeerflowStatus, student]
  );

  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handleStorage = () => {
      setStudent(getStudentSnapshot());
    };

    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, []);

  return (
    <div className={`workspace-shell${sidebarCollapsed ? ' is-sidebar-collapsed' : ''}`}>
      <Sidebar
        collapsed={sidebarCollapsed}
        mobileOpen={mobileSidebarOpen}
        onToggleCollapse={() => setSidebarCollapsed((value) => !value)}
        onCloseMobile={() => setMobileSidebarOpen(false)}
      />

      <button
        type="button"
        className={`workspace-scrim${mobileSidebarOpen ? ' is-visible' : ''}`}
        onClick={() => setMobileSidebarOpen(false)}
        aria-label="关闭工作台导航"
        aria-hidden={!mobileSidebarOpen}
        tabIndex={mobileSidebarOpen ? 0 : -1}
      />

      <div className="workspace-main">
        <ContextBar
          student={student}
          deerflowStatus={deerflowStatus}
          mobileSidebarOpen={mobileSidebarOpen}
          onMenuClick={() => setMobileSidebarOpen(true)}
        />
        <main className="workspace-content">
          <Outlet context={outletContext} />
        </main>
      </div>
    </div>
  );
};

export default WorkspaceLayout;
