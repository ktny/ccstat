import React from 'react';
import { Box, Text } from 'ink';
import { ProgressUpdate } from '../../utils/progressTracker';

interface LoadingScreenProps {
  progress: ProgressUpdate;
}

export const LoadingScreen: React.FC<LoadingScreenProps> = ({ progress }) => {
  const { totalFiles, processedFiles, currentFile, currentProject, stage } = progress;

  const getStageMessage = (): string => {
    switch (stage) {
      case 'discovering':
        return '🔍 Discovering Claude project files...';
      case 'processing':
        return '📁 Processing project files...';
      case 'analyzing':
        return '📊 Analyzing sessions and calculating timelines...';
      case 'complete':
        return '✅ Processing complete!';
      default:
        return '🔄 Loading ccstat...';
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

  const getCurrentFileName = (): string => {
    if (!currentFile) return '';

    // Extract just the filename from the full path
    const fileName = currentFile.split('/').pop() || currentFile;
    return fileName;
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

      {stage === 'processing' && totalFiles > 0 && (
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

          {currentProject && (
            <Box marginBottom={1}>
              <Text>
                Current project: <Text color="yellow">{currentProject}</Text>
              </Text>
            </Box>
          )}

          {currentFile && (
            <Box marginBottom={1}>
              <Text>
                Processing: <Text color="gray">{getCurrentFileName()}</Text>
              </Text>
            </Box>
          )}
        </>
      )}

      {stage === 'analyzing' && (
        <Box marginBottom={1}>
          <Text>
            <Text color="cyan">{'█'.repeat(40)}</Text> 100%
          </Text>
        </Box>
      )}
    </Box>
  );
};
