import React from 'react';
import { Box, Text } from 'ink';
import type { SessionTimeline } from '@/models';
import { formatDuration } from '@/utils/time';

interface ProjectTableProps {
  sessions: SessionTimeline[];
  showWorktree: boolean;
}

export const ProjectTable: React.FC<ProjectTableProps> = ({ sessions, showWorktree }) => {
  if (sessions.length === 0) {
    return (
      <Box marginTop={1}>
        <Text dimColor>No projects found with activity in the specified time range.</Text>
      </Box>
    );
  }

  // Group sessions by parent project if not in worktree mode
  const displaySessions = groupSessions(sessions, showWorktree);

  return (
    <Box flexDirection="column" marginTop={1}>
      <Box>
        <Text bold underline>
          Projects with Activity
        </Text>
      </Box>

      <Box marginTop={1} flexDirection="column">
        {displaySessions.map((session, index) => (
          <ProjectRow key={index} session={session} />
        ))}
      </Box>

      <Box marginTop={1}>
        <Text dimColor>Total projects: {displaySessions.length}</Text>
      </Box>
    </Box>
  );
};

interface ProjectRowProps {
  session: SessionTimeline;
}

const ProjectRow: React.FC<ProjectRowProps> = ({ session }) => {
  const isChild = Boolean(session.parentProject);
  const prefix = isChild ? '└─ ' : '';

  const eventCount = session.events.length;
  const duration = formatDuration(session.activeDuration);
  const timeRange = `${session.startTime.toLocaleTimeString()} - ${session.endTime.toLocaleTimeString()}`;

  return (
    <Box>
      <Text>
        {prefix}
        <Text color="cyan" bold>
          {session.project}
        </Text>
        <Text dimColor> │ </Text>
        <Text color="green">{duration}</Text>
        <Text dimColor> │ </Text>
        <Text color="yellow">{eventCount} events</Text>
        <Text dimColor> │ </Text>
        <Text dimColor>{timeRange}</Text>
      </Text>
    </Box>
  );
};

function groupSessions(sessions: SessionTimeline[], showWorktree: boolean): SessionTimeline[] {
  if (showWorktree) {
    return sessions;
  }

  // Group by parent project
  const grouped = new Map<string, SessionTimeline[]>();
  const standalone: SessionTimeline[] = [];

  for (const session of sessions) {
    if (session.parentProject) {
      const key = session.parentProject;
      if (!grouped.has(key)) {
        grouped.set(key, []);
      }
      grouped.get(key)!.push(session);
    } else {
      standalone.push(session);
    }
  }

  const result: SessionTimeline[] = [];

  // Add standalone projects
  result.push(...standalone);

  // Add grouped projects with their children
  for (const [parentName, children] of grouped.entries()) {
    // Skip if no children (shouldn't happen but TypeScript requires this check)
    if (children.length === 0) continue;

    // Create a parent session that aggregates the children
    const allEvents = children.flatMap((child) => child.events);
    const startTimes = children.map((c) => c.startTime.getTime());
    const endTimes = children.map((c) => c.endTime.getTime());
    const totalDuration = children.reduce((sum, c) => sum + c.activeDuration, 0);

    const parentSession: SessionTimeline = {
      project: parentName,
      directory: children[0]!.directory, // Use first child's directory
      events: allEvents,
      activeDuration: totalDuration,
      startTime: new Date(Math.min(...startTimes)),
      endTime: new Date(Math.max(...endTimes)),
    };

    result.push(parentSession);

    // Add children as sub-projects
    for (const child of children) {
      result.push({
        ...child,
        parentProject: parentName,
      });
    }
  }

  return result;
}
