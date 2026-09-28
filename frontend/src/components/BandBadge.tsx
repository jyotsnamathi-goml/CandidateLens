import React from 'react';
import { CheckCircle2, AlertCircle, AlertTriangle } from 'lucide-react';
import { ReadinessBand } from '../api/types';

interface Props {
  band: ReadinessBand;
  size?: 'sm' | 'md' | 'lg';
}

export const BandBadge: React.FC<Props> = ({ band, size = 'md' }) => {
  const configs = {
    'Strong Readiness': {
      bg: 'bg-emerald-500/10 border-emerald-500/30 text-emerald-400',
      glow: 'shadow-emerald-500/10 shadow-lg',
      icon: CheckCircle2,
    },
    'Moderate Readiness': {
      bg: 'bg-amber-500/10 border-amber-500/30 text-amber-400',
      glow: 'shadow-amber-500/10 shadow-lg',
      icon: AlertTriangle,
    },
    'Needs Verification': {
      bg: 'bg-rose-500/10 border-rose-500/30 text-rose-400',
      glow: 'shadow-rose-500/10 shadow-lg',
      icon: AlertCircle,
    },
  };

  const config = configs[band] || configs['Moderate Readiness'];
  const Icon = config.icon;

  const sizeClasses = {
    sm: 'px-2 py-0.5 text-xs',
    md: 'px-3 py-1.5 text-sm',
    lg: 'px-4 py-2 text-base font-semibold',
  };

  const iconSizes = {
    sm: 'w-3.5 h-3.5',
    md: 'w-4 h-4',
    lg: 'w-5 h-5',
  };

  return (
    <span
      className={`inline-flex items-center space-x-1.5 rounded-full border font-medium ${config.bg} ${config.glow} ${sizeClasses[size]}`}
    >
      <Icon className={`${iconSizes[size]} flex-shrink-0`} />
      <span>{band}</span>
    </span>
  );
};
