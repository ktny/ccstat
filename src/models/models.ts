import { z } from 'zod';

export const EventSchema = z
  .object({
    timestamp: z.string(),
    sessionId: z.string().optional(),
    cwd: z.string().optional(),
    message: z.any().optional(), // More flexible to handle various message formats
    usage: z
      .object({
        inputTokens: z.number().optional(),
        outputTokens: z.number().optional(),
        cacheWriteTokens: z.number().optional(),
        cacheReadTokens: z.number().optional(),
      })
      .optional(),
    type: z.string().optional(),
    uuid: z.string().optional(),
  })
  .passthrough(); // Allow additional properties

export type Event = z.infer<typeof EventSchema>;

export interface Timeline {
  projectName: string;
  events: Event[];
  eventCount: number;
  activeDuration: number;
  startTime: Date;
  endTime: Date;
}
