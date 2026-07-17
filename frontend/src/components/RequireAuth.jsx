import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { getAuthToken, getStoredStudent } from '../api/client';

const RequireAuth = () => {
  const location = useLocation();
  const token = getAuthToken();

  if (!token) {
    return (
      <Navigate
        to="/login"
        replace
        state={{ from: `${location.pathname}${location.search}${location.hash}` }}
      />
    );
  }

  const student = getStoredStudent();
  const isOnboardingRoute = location.pathname === '/onboarding';

  if (student && student.onboarding_completed === false && !isOnboardingRoute) {
    return <Navigate to="/onboarding" replace />;
  }

  if (student && student.onboarding_completed !== false && isOnboardingRoute) {
    return <Navigate to="/app/today" replace />;
  }

  return <Outlet />;
};

export default RequireAuth;
