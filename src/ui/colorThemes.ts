import chalk from 'chalk';

export type ColorTheme = 'blue' | 'green' | 'orange' | 'purple';

export type ColorScheme = (string | ((text: string) => string))[];

// Helper function to create hex color gradients for same hue with high contrast differences
const createHexGradient = (hexColors: string[]): ColorScheme =>
  hexColors.map(color => (text: string) => chalk.hex(color)(text));

export const COLOR_THEMES: Record<ColorTheme, ColorScheme> = {
  green: createHexGradient(['#edf8fb', '#b2e2e2', '#66c2a4', '#2ca25f', '#006d2c']),
  blue: createHexGradient(['#9ca3af', '#bbf7d0', '#4ade80', '#16a34a', '#14532d']),
  orange: createHexGradient(['#9ca3af', '#fed7aa', '#fb923c', '#ea580c', '#9a3412']),
  purple: createHexGradient(['#9ca3af', '#ddd6fe', '#a78bfa', '#7c3aed', '#4c1d95']),
};

export function getColorScheme(theme: ColorTheme): ColorScheme {
  return COLOR_THEMES[theme];
}

// Helper function to get border color for each theme
export function getBorderColor(theme: ColorTheme): string {
  switch (theme) {
    case 'blue':
      return 'blue'; // Blue theme
    case 'green':
      return 'green'; // Green theme
    case 'orange':
      return 'yellow'; // Orange theme (closest terminal color)
    case 'purple':
      return 'magenta'; // Purple theme
    default:
      return 'green'; // Keep classic cyan for classic theme
  }
}
