import { useEffect } from 'react';

const Toast = ({ message, type = 'success', onClose, duration = 4000 }) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose?.();
    }, duration);
    return () => clearTimeout(timer);
  }, [duration, onClose]);

  return (
    <div className={`toast ${type === 'error' ? 'toast-error' : ''}`}>
      <div className="toast-title">{type === 'error' ? '出错了' : '操作成功'}</div>
      <div className="toast-message">{message}</div>
    </div>
  );
};

export default Toast;
