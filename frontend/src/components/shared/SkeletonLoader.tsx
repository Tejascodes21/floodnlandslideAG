import React from 'react';

interface SkeletonProps {
  className?: string;
}

export const Skeleton: React.FC<SkeletonProps> = ({ className = '' }) => {
  return (
    <div className={`animate-pulse bg-slate-800/40 rounded ${className}`} />
  );
};

export const MapSkeleton: React.FC = () => {
  return (
    <div className="w-full h-full min-h-[350px] relative bg-slate-900/60 rounded-xl overflow-hidden flex flex-col justify-between p-4 border border-slate-800">
      <div className="flex justify-between items-center z-10">
        <Skeleton className="h-4 w-32" />
        <Skeleton className="h-6 w-20" />
      </div>
      <div className="absolute inset-0 flex items-center justify-center pointer-events-none">
        <div className="relative w-16 h-16 rounded-full border border-blue-500/20 flex items-center justify-center">
          <div className="absolute w-24 h-24 rounded-full border border-blue-500/10 animate-ping" />
          <div className="w-8 h-8 rounded-full bg-blue-500/10 border border-blue-500/40 animate-pulse" />
        </div>
      </div>
      <div className="flex justify-between items-center z-10">
        <Skeleton className="h-8 w-28" />
        <Skeleton className="h-4 w-20" />
      </div>
    </div>
  );
};

export const ChartSkeleton: React.FC = () => {
  return (
    <div className="w-full h-[260px] bg-slate-900/30 p-5 rounded-xl border border-slate-900 flex flex-col justify-between">
      <div className="flex justify-between items-center">
        <Skeleton className="h-4 w-40" />
        <div className="flex gap-2">
          <Skeleton className="h-4 w-12" />
          <Skeleton className="h-4 w-12" />
        </div>
      </div>
      <div className="flex-1 flex items-end gap-4 px-2 py-4">
        <Skeleton className="h-[30%] w-full" />
        <Skeleton className="h-[55%] w-full" />
        <Skeleton className="h-[80%] w-full" />
        <Skeleton className="h-[40%] w-full" />
        <Skeleton className="h-[65%] w-full" />
        <Skeleton className="h-[90%] w-full" />
        <Skeleton className="h-[25%] w-full" />
      </div>
      <div className="flex justify-between items-center px-1">
        <Skeleton className="h-3 w-8" />
        <Skeleton className="h-3 w-8" />
        <Skeleton className="h-3 w-8" />
        <Skeleton className="h-3 w-8" />
      </div>
    </div>
  );
};

export const TelemetrySkeleton: React.FC = () => {
  return (
    <div className="space-y-3">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="p-3 bg-slate-950/40 rounded-xl border border-slate-900/60 flex justify-between items-center">
          <div className="space-y-1.5">
            <Skeleton className="h-3 w-12" />
            <Skeleton className="h-4 w-36" />
          </div>
          <div className="flex gap-4 items-center">
            <div className="space-y-1 text-right">
              <Skeleton className="h-3 w-8 ml-auto" />
              <Skeleton className="h-4 w-16" />
            </div>
            <Skeleton className="h-5 w-16" />
          </div>
        </div>
      ))}
    </div>
  );
};
