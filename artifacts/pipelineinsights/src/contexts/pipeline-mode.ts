import { createContext, useContext } from 'react';

export type PipelineDataMode = 'real' | 'demo';

export const PipelineModeContext = createContext<{
  mode: PipelineDataMode;
  setMode: (mode: PipelineDataMode) => void;
} | null>(null);

export function usePipelineMode() {
  const context = useContext(PipelineModeContext);
  if (!context) {
    throw new Error('usePipelineMode must be used within AppShell.');
  }
  return context;
}