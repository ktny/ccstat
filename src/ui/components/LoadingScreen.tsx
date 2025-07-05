import React from 'react';
import { Box, Text } from 'ink';
import { ProgressUpdate } from '../../utils/progressTracker';

interface LoadingScreenProps {
  progress: ProgressUpdate;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ progress }) => {
  const { totalFiles, processedFiles } = progress;

  const getStageMessage = (): string => {
    if (totalFiles === 0) {
      return '🔍 Discovering Claude project files...';
    } else if (processedFiles < totalFiles) {
      return '📁 Processing project files...';
    } else {
      return '📊 Analyzing sessions and calculating timelines...';
    }
  };

  const getProgressBar = (): string => {
    if (totalFiles === 0) return '';

    const percentage = Math.round((processedFiles / totalFiles) * 100);
    const barLength = 40;
    const filledLength = Math.round((percentage / 100) * barLength);
    const emptyLength = barLength - filledLength;

    const filledBar = '█'.repeat(filledLength);
    const emptyBar = '░'.repeat(emptyLength);

    return `${filledBar}${emptyBar}`;
  };

  const getProgressPercentage = (): number => {
    if (totalFiles === 0) return 0;
    return Math.round((processedFiles / totalFiles) * 100);
  };

  return (
    <Box flexDirection="column" paddingX={2} paddingY={1}>
      <Box marginBottom={1}>
        <Text bold color="cyan">
          🔄 Loading ccstat...
        </Text>
      </Box>

      <Box marginBottom={1}>
        <Text>{getStageMessage()}</Text>
      </Box>

      {totalFiles > 0 && (
        <>
          <Box marginBottom={1}>
            <Text>
              <Text color="cyan">{getProgressBar()}</Text> {getProgressPercentage()}%
            </Text>
          </Box>

          <Box marginBottom={1}>
            <Text>
              Files processed: <Text color="green">{processedFiles}</Text> /{' '}
              <Text color="blue">{totalFiles}</Text>
            </Text>
          </Box>
        </>
      )}
    </Box>
  );
};
