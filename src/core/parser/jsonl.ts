import { createReadStream } from 'fs';
import { createInterface } from 'readline';
import type { MessageEvent, TimeRange } from '@/models';
import { SessionEventSchema } from '@/models';
import { isWithinTimeRange } from '@/utils/time';

interface ParseResult {
  events: MessageEvent[];
  totalLines: number;
  skippedLines: number;
}

export async function parseJSONLFile(
  filePath: string,
  timeRange: TimeRange,
  debug: boolean = false,
): Promise<ParseResult> {
  const events: MessageEvent[] = [];
  let totalLines = 0;
  let skippedLines = 0;

  const fileStream = createReadStream(filePath, { encoding: 'utf8' });
  const rl = createInterface({
    input: fileStream,
    crlfDelay: Infinity, // Handle Windows line endings
  });

  for await (const line of rl) {
    totalLines++;

    if (!line.trim()) {
      skippedLines++;
      continue;
    }

    try {
      const rawEvent: unknown = JSON.parse(line);

      // Extract required fields
      const timestamp = (rawEvent as Record<string, unknown>).timestamp;
      if (!timestamp || typeof timestamp !== 'string' || !isWithinTimeRange(timestamp, timeRange)) {
        skippedLines++;
        continue;
      }

      // Validate and parse event using Zod schema
      const parseResult = SessionEventSchema.safeParse(rawEvent);
      if (!parseResult.success) {
        if (debug) {
          console.error(
            `Invalid event format in ${filePath}:${totalLines}:`,
            parseResult.error.message,
          );
        }
        skippedLines++;
        continue;
      }

      // Only include message events (user/assistant) for analysis
      if (parseResult.data.type === 'user' || parseResult.data.type === 'assistant') {
        events.push(parseResult.data);
      } else {
        skippedLines++;
      }
    } catch (error) {
      // Skip malformed JSON lines
      if (debug) {
        console.error(`Malformed JSON in ${filePath}:${totalLines}:`, error);
      }
      skippedLines++;
    }
  }

  if (debug && totalLines > 0) {
    console.error(
      `File ${filePath}: ${totalLines} lines, ${events.length} events, ${skippedLines} skipped`,
    );
  }

  return { events, totalLines, skippedLines };
}

export async function parseFilesInParallel(
  filePaths: string[],
  timeRange: TimeRange,
  debug: boolean = false,
): Promise<MessageEvent[]> {
  const parsePromises = filePaths.map((filePath) => parseJSONLFile(filePath, timeRange, debug));

  const results = await Promise.all(parsePromises);

  const allEvents = results.flatMap((result) => result.events);

  if (debug) {
    const totalLines = results.reduce((sum, result) => sum + result.totalLines, 0);
    const totalSkipped = results.reduce((sum, result) => sum + result.skippedLines, 0);
    console.error(
      `Parsed ${filePaths.length} files: ${totalLines} total lines, ${allEvents.length} events, ${totalSkipped} skipped`,
    );
  }

  // Sort events by timestamp
  return allEvents.sort(
    (a, b) => new Date(a.timestamp).getTime() - new Date(b.timestamp).getTime(),
  );
}
