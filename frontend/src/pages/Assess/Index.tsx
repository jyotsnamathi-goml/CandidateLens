import React, { useState } from 'react';
import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { api } from '../../api/client';
import { AssessmentSession } from '../../api/types';
import { AssessWelcome } from './Welcome';
import { AssessQuestionScreen } from './QuestionScreen';
import { AssessCompleted } from './Completed';
import { AssessExpired } from './Expired';

export const AssessIndex: React.FC = () => {
  const { token } = useParams<{ token: string }>();
  const [submitting, setSubmitting] = useState(false);

  const { data: session, isLoading, error, refetch } = useQuery<AssessmentSession>({
    queryKey: ['assessmentSession', token],
    queryFn: () => api.getAssessmentSession(token!),
    enabled: !!token,
    retry: false,
  });

  if (isLoading) {
    return <div className="min-h-screen flex items-center justify-center text-xs text-slate-500 animate-pulse">Loading assessment...</div>;
  }

  if (error || !session) {
    return <AssessExpired />;
  }

  if (session.state === 'SUBMITTED' || session.state === 'EVALUATING' || session.state === 'DONE') {
    return <AssessCompleted />;
  }

  if (session.state === 'EXPIRED') {
    return <AssessExpired />;
  }

  const handleStart = () => {
    // Calling submitAnswer with empty string or refetching triggers ACTIVE state transition
    refetch();
  };

  const handleAnswerSubmit = async (answer: string, secondsTaken: number) => {
    setSubmitting(true);
    try {
      const nextStep = await api.submitAnswer(token!, answer, secondsTaken);
      refetch();
    } catch (err: any) {
      alert(err.message || 'Failed to submit answer.');
    } finally {
      setSubmitting(false);
    }
  };

  if (session.state === 'NOT_STARTED') {
    return <AssessWelcome session={session} onStart={handleStart} />;
  }

  return (
    <AssessQuestionScreen
      session={session}
      onSubmit={handleAnswerSubmit}
      submitting={submitting}
    />
  );
};
