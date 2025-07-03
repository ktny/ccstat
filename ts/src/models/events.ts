import { z } from 'zod';

export const SessionEventSchema = z.object({
  timestamp: z.string(),
  sessionId: z.string(),
  cwd: z.string(),
  message: z.string().optional(),
  usage: z.object({
    inputTokens: z.number(),
    outputTokens: z.number(),
    cacheWriteTokens: z.number().optional(),
    cacheReadTokens: z.number().optional(),
  }).optional(),
});

export type SessionEvent = z.infer<typeof SessionEventSchema>;

export interface SessionTimeline {
  projectName: string;
  directory: string;
  repository?: string;
  isChild?: boolean;
  events: SessionEvent[];
  eventCount: number;
  activeDuration: number;
  startTime: Date;
  endTime: Date;
}
