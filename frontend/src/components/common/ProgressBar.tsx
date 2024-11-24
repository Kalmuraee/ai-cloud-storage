import React from 'react';
import clsx from 'clsx';

interface ProgressBarProps {
  progress: number;
  size?: 'sm' | 'md' | 'lg';
  color?: 'blue' | 'green' | 'red' | 'yellow';
  showLabel?: boolean;
  className?: string;
}

const ProgressBar: React.FC<ProgressBarProps> = ({
  progress,
  size = 'md',
  color = 'blue',
  showLabel = true,
  className,
}) => {
  const normalizedProgress = Math.min(Math.max(progress, 0), 100);

  const sizes = {
    sm: 'h-1',
    md: 'h-2',
    lg: 'h-3',
  };

  const colors = {
    blue: 'bg-blue-600',
    green: 'bg-green-600',
    red: 'bg-red-600',
    yellow: 'bg-yellow-600',
  };

  return (
    <div className={clsx('w-full', className)}>
      <div className="relative">
        <div
          className={clsx(
            'w-full rounded-full bg-gray-200',
            sizes[size]
          )}
        >
          <div
            className={clsx(
              'rounded-full transition-all duration-300 ease-in-out',
              sizes[size],
              colors[color]
            )}
            style={{ width: `${normalizedProgress}%` }}
          />
        </div>
      </div>
      {showLabel && (
        <div className="mt-1 text-right text-sm text-gray-600">
          {Math.round(normalizedProgress)}%
        </div>
      )}
    </div>
  );
};

export default ProgressBar;
