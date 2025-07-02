import { z } from 'zod';

// Base schema for Claude Code log events
const BaseEventSchema = z.object({
  timestamp: z.string().optional(), // Some events like summary don't have timestamp
  sessionId: z.string().optional(),
  cwd: z.string().optional(),
  uuid: z.string().optional(),
  type: z.string(),
});

// Schema for summary events
const SummaryEventSchema = BaseEventSchema.extend({
  type: z.literal('summary'),
  summary: z.string(),
  leafUuid: z.string(),
});

// Schema for user/assistant message events
const MessageEventSchema = BaseEventSchema.extend({
  type: z.union([z.literal('user'), z.literal('assistant')]),
  timestamp: z.string(), // Required for message events
  sessionId: z.string(), // Required for message events
  cwd: z.string(), // Required for message events
  parentUuid: z.string().nullable(),
  isSidechain: z.boolean(),
  userType: z.string(),
  version: z.string(),
  message: z
    .object({
      role: z.string(),
      content: z.union([z.string(), z.array(z.any())]), // Content can be string or array
    })
    .passthrough(), // Allow additional fields
  requestId: z.string().optional(),
  toolUseResult: z.any().optional(),
});

// Union of all event types
export const SessionEventSchema = z.union([SummaryEventSchema, MessageEventSchema]);

export type SessionEvent = z.infer<typeof SessionEventSchema>;

// Type for message events specifically (what we use for analysis)
export type MessageEvent = z.infer<typeof MessageEventSchema>;

export interface SessionTimeline {
  project: string;
  directory: string;
  events: MessageEvent[];
  activeDuration: number; // in seconds
  startTime: Date;
  endTime: Date;
  parentProject?: string | undefined; // For worktree mode
}

export interface TimeRange {
  start: Date;
  end: Date;
}

export interface CLIOptions {
  days?: number;
  hours?: number;
  project?: string;
  worktree: boolean;
  debug: boolean;
  version: boolean;
}
