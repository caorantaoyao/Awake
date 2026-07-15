import { useCallback, useEffect, useMemo, useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import ContextBar from '../components/ContextBar';
import Sidebar from '../components/Sidebar';
import { getDeerflowStatus, getModels, getStoredStudent } from '../api/client';

const createPendingDeerflowStatus = () => ({
  online: null,
  label: '状态加载中',
  model: null,
  assistant_id: null,
  error: null
});

const getRequestErrorMessage = (error, fallback) =>
  error?.response?.data?.detail || error?.message || fallback;

const getFirstModelName = (modelsResponse) => {
  if (modelsResponse?.online === false) return null;
  const firstModel = modelsResponse?.models?.[0];
  return firstModel?.name || firstModel?.id || null;
};

const normalizeDeerflowStatus = (statusResponse, modelsResponse) => {
  const online = statusResponse?.online === true;
  const offline = statusResponse?.online === false;
  const model = statusResponse?.model || getFirstModelName(modelsResponse);

  return {
    ...(statusResponse || {}),
    online: online ? true : offline ? false : null,
    label: online ? '在线' : offline ? '离线' : '状态未知',
    model,
    assistant_id: statusResponse?.assistant_id || null,
    error: statusResponse?.error || modelsResponse?.error || null
  };
};

const fetchDeerflowSnapshot = async () => {
  const [statusResult, modelsResult] = await Promise.allSettled([
    getDeerflowStatus(),
    getModels()
  ]);

  if (statusResult.status === 'fulfilled') {
    return normalizeDeerflowStatus(
      statusResult.value,
      modelsResult.status === 'fulfilled' ? modelsResult.value : null
    );
  }

  return {
    online: false,
    label: '离线',
    model: null,
    assistant_id: null,
    error: getRequestErrorMessage(statusResult.reason, 'DeerFlow 状态接口请求失败')
  };
};

const safeGetStoredStudent = () => {
  try {
    return getStoredStudent();
  } catch {
    return null;
  }
};

const getStudentSnapshot = (search) => {
  const params = new URLSearchParams(search);
  const queryEmail = params.get('email');
  const storedStudent = safeGetStoredStudent();

  if (!queryEmail) return storedStudent;
  if (storedStudent?.email === queryEmail) {
    return { ...storedStudent, email: queryEmail };
  }
  return { email: queryEmail };
};

const WorkspaceLayout = () => {
  const location = useLocation();
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileSidebarOpen, setMobileSidebarOpen] = useState(false);
  const [student, setStudent] = useState(() => getStudentSnapshot(location.search));
  const [deerflowStatus, setDeerflowStatus] = useState(createPendingDeerflowStatus);
  const currentModel = deerflowStatus.model;

  const refreshDeerflowStatus = useCallback(async () => {
    const nextStatus = await fetchDeerflowSnapshot();
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
    let alive = true;

    const loadDeerflowStatus = async () => {
      const nextStatus = await fetchDeerflowSnapshot();
      if (alive) {
        setDeerflowStatus(nextStatus);
      }
    };

    loadDeerflowStatus();
    return () => {
      alive = false;
    };
  }, []);

  useEffect(() => {
    setStudent(getStudentSnapshot(location.search));
  }, [location.search]);

  useEffect(() => {
    setMobileSidebarOpen(false);
  }, [location.pathname]);

  useEffect(() => {
    const handleStorage = () => {
      setStudent(getStudentSnapshot(location.search));
    };

    window.addEventListener('storage', handleStorage);
    return () => window.removeEventListener('storage', handleStorage);
  }, [location.search]);

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
          currentModel={currentModel}
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
