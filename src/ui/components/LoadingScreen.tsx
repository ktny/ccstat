import React from 'react';
import { Box, Text } from 'ink';
import { ProgressUpdate } from '../../utils/progressTracker';

interface LoadingScreenProps {
  progress: ProgressUpdate;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ progress }) => {
  const { totalFiles, processedFiles } = progress;

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
    <Box flexDirection="column" paddingLeft={1} paddingBottom={1}>
      {totalFiles > 0 && (
        <>
          <Box>
            <Text>
              <Text color="cyan">{getProgressBar()}</Text> {getProgressPercentage()}%
            </Text>
          </Box>
          <Box>
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
