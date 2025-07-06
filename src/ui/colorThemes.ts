import chalk from 'chalk';

export type ColorTheme = 'github' | 'ocean' | 'sunset' | 'violet';

export type ColorScheme = (string | ((text: string) => string))[];

// Helper function to create hex color gradients for same hue with high contrast differences
const createHexGradient = (hexColors: string[]): ColorScheme =>
  hexColors.map(color => (text: string) => chalk.hex(color)(text));

export const COLOR_THEMES: Record<ColorTheme, ColorScheme> = {
  github: createHexGradient(['#edf8fb', '#b2e2e2', '#66c2a4', '#2ca25f', '#006d2c']),
  ocean: createHexGradient(['#f1eef6', '#bdc9e1', '#74a9cf', '#2b8cbe', '#045a8d']),
  sunset: createHexGradient(['#fef0d9', '#fdcc8a', '#fc8d59', '#e34a33', '#b30000']),
  violet: createHexGradient(['#edf8fb', '#b3cde3', '#8c96c6', '#8856a7', '#810f7c']),
};

export function getColorScheme(theme: ColorTheme): ColorScheme {
  return COLOR_THEMES[theme];
}

// Helper function to get border color for each theme
export function getBorderColor(theme: ColorTheme): string {
  switch (theme) {
    case 'github':
      return 'green';
    case 'ocean':
      return 'blue';
    case 'sunset':
      return 'yellow';
    case 'violet':
      return 'magenta';
    default:
      return 'green';
  }
}
