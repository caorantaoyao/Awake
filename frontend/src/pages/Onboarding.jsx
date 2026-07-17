import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { completeOnboarding as completeOnboardingApi, getStoredStudent, updateStoredStudent } from '../api/client';
import { ONBOARDING_STEPS } from '../config/onboarding';

const STEPS = ONBOARDING_STEPS;

const Onboarding = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [selectedInStep, setSelectedInStep] = useState(null);
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [showComplete, setShowComplete] = useState(false);
  const [completing, setCompleting] = useState(false);
  const [studentName, setStudentName] = useState('同学');
  const [visibleLines, setVisibleLines] = useState(0);
  const [optionsVisible, setOptionsVisible] = useState(false);

  const currentStep = STEPS[step];
  const isLastStep = step === STEPS.length - 1;
  const totalSteps = STEPS.length;

  useEffect(() => {
    const stored = getStoredStudent();
    if (stored?.name) {
      setStudentName(stored.name);
    }
  }, []);

  const questionText = typeof currentStep.question === 'function'
    ? currentStep.question(studentName, answers)
    : currentStep.question;
  const lines = questionText.split('\n').filter(l => l.trim());

  useEffect(() => {
    setVisibleLines(0);
    setOptionsVisible(false);
    setSelectedInStep(null);

    const lineTimers = [];
    lines.forEach((_, i) => {
      lineTimers.push(setTimeout(() => {
        setVisibleLines(i + 1);
      }, 200 + i * 350));
    });

    const optionsTimer = setTimeout(() => {
      setOptionsVisible(true);
    }, 200 + lines.length * 350 + 150);

    return () => {
      lineTimers.forEach(clearTimeout);
      clearTimeout(optionsTimer);
    };
  }, [step]);

  const getOptions = useCallback(() => {
    if (typeof currentStep.getOptions === 'function') {
      return currentStep.getOptions(answers);
    }
    return currentStep.options || [];
  }, [currentStep, answers]);

  const handleSelect = (option) => {
    if (isTransitioning || completing) return;

    setSelectedInStep(option.value);
    setIsTransitioning(true);

    const newAnswers = { ...answers };
    if (currentStep.multiSelect) {
      const current = newAnswers[currentStep.id] || [];
      newAnswers[currentStep.id] = current.includes(option.value)
        ? current.filter(v => v !== option.value)
        : [...current, option.value];
    } else {
      newAnswers[currentStep.id] = [option.value];
    }
    setAnswers(newAnswers);

    setTimeout(() => {
      if (isLastStep) {
        handleComplete(newAnswers);
      } else {
        setStep(prev => prev + 1);
        setIsTransitioning(false);
      }
    }, 550);
  };

  const handleUncertain = () => {
    if (!currentStep.uncertain) return;
    handleSelect({ label: currentStep.uncertain.label, value: currentStep.uncertain.value, isUncertain: true });
  };

  const handleComplete = async (finalAnswers) => {
    setCompleting(true);
    try {
      const interestTags = finalAnswers.interest || [];
      const confusionTags = finalAnswers.confusion || [];
      const learningStyle = finalAnswers.style?.[0] || null;

      const result = await completeOnboardingApi({
        interest_tags: interestTags,
        confusion_tags: confusionTags,
        learning_style: learningStyle,
      });

      if (result.success && result.data?.student) {
        updateStoredStudent(result.data.student);
      }

      if (result.success && result.data?.welcome_message) {
        localStorage.setItem('awaken_welcome_message', result.data.welcome_message);
      }

      setTimeout(() => {
        setShowComplete(true);
        setTimeout(() => {
          navigate('/app/chat', { replace: true });
        }, 1800);
      }, 400);
    } catch (err) {
      console.error('Onboarding complete failed:', err);
      setTimeout(() => {
        setShowComplete(true);
        setTimeout(() => {
          navigate('/app/today', { replace: true });
        }, 1500);
      }, 400);
    }
  };

  const options = getOptions();
  const progress = ((step + (isTransitioning && !isLastStep ? 1 : 0)) / totalSteps) * 100;

  return (
    <div className="onboarding-page">
      <div className="onboarding-bg">
        <div className="onboarding-orb onboarding-orb-1" />
        <div className="onboarding-orb onboarding-orb-2" />
        <div className="onboarding-orb onboarding-orb-3" />
      </div>

      <div className="onboarding-container">
        <div className="onboarding-progress">
          <div className="onboarding-progress-track">
            <div
              className="onboarding-progress-fill"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="onboarding-progress-steps">
            {STEPS.map((_, i) => (
              <div
                key={i}
                className={`onboarding-step-dot ${i <= step ? 'is-active' : ''} ${i < step ? 'is-done' : ''}`}
              />
            ))}
          </div>
        </div>

        {showComplete ? (
          <div className="onboarding-complete" key="complete">
            <div className="onboarding-complete-icon">
              <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14" />
                <polyline points="22 4 12 14.01 9 11.01" />
              </svg>
            </div>
            <h2>准备好了！</h2>
            <p>正在为你打开和小海的对话...</p>
          </div>
        ) : (
          <div className="onboarding-chat" key={`step-${step}`}>
            <div className="onboarding-avatar-wrap">
              <div className="onboarding-avatar">
                <span>🌊</span>
              </div>
              <div className="onboarding-avatar-ring" />
            </div>

            <div className="onboarding-bubble">
              {lines.map((line, i) => (
                <p
                  key={i}
                  className={`onboarding-line ${i < visibleLines ? 'is-visible' : ''}`}
                >
                  {line}
                </p>
              ))}
            </div>

            <div className={`onboarding-tags ${optionsVisible ? 'is-visible' : ''}`}>
              {options.map((opt, i) => {
                const isSelected = selectedInStep === opt.value;
                return (
                  <button
                    key={opt.value}
                    className={`onboarding-tag ${isSelected ? 'is-selected' : ''}`}
                    onClick={() => handleSelect(opt)}
                    disabled={isTransitioning}
                    style={{ animationDelay: `${i * 60}ms` }}
                  >
                    <span className="onboarding-tag-emoji">{opt.emoji}</span>
                    <span className="onboarding-tag-label">{opt.label}</span>
                  </button>
                );
              })}
              {currentStep.uncertain && (
                <button
                  className={`onboarding-tag onboarding-tag-uncertain ${selectedInStep === currentStep.uncertain.value ? 'is-selected' : ''}`}
                  onClick={handleUncertain}
                  disabled={isTransitioning}
                  style={{ animationDelay: `${options.length * 60}ms` }}
                >
                  <span className="onboarding-tag-emoji">{currentStep.uncertain.emoji}</span>
                  <span className="onboarding-tag-label">{currentStep.uncertain.label}</span>
                </button>
              )}
            </div>

            <div className="onboarding-step-indicator">
              <span>{step + 1}</span> / {totalSteps}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default Onboarding;
