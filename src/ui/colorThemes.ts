import chalk from 'chalk';

export type ColorTheme = 'blue' | 'green' | 'orange' | 'purple' | 'classic';

export interface ColorScheme {
  name: string;
  colors: (string | ((text: string) => string))[];
}

// Helper function to create hex color gradients for same hue with high contrast differences
const createHexGradient = (hexColors: string[], name: string): ColorScheme => ({
  name: `${name} (Gradient)`,
  colors: hexColors.map(color => (text: string) => chalk.hex(color)(text)),
});

export const COLOR_THEMES: Record<ColorTheme, ColorScheme> = {
  blue: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#bfdbfe',  // Blue-200 (very light blue)
    '#60a5fa',  // Blue-400 (medium blue)
    '#2563eb',  // Blue-600 (bright blue)
    '#1e3a8a',  // Blue-800 (very dark blue)
  ], 'Blue'),

  green: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#bbf7d0',  // Green-200 (very light green)
    '#4ade80',  // Green-400 (medium green)
    '#16a34a',  // Green-600 (bright green)
    '#14532d',  // Green-800 (very dark green)
  ], 'Green'),

  orange: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#fed7aa',  // Orange-200 (very light orange)
    '#fb923c',  // Orange-400 (medium orange)
    '#ea580c',  // Orange-600 (bright orange)
    '#9a3412',  // Orange-800 (very dark orange)
  ], 'Orange'),

  purple: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#ddd6fe',  // Violet-200 (very light purple)
    '#a78bfa',  // Violet-400 (medium purple)
    '#7c3aed',  // Violet-600 (bright purple)
    '#4c1d95',  // Violet-800 (very dark purple)
  ], 'Purple'),

  classic: {
    name: 'Classic (GitHub Style)',
    colors: ['gray', 'green', 'greenBright', 'yellow', 'red'],
  },
};

export function getColorScheme(theme: ColorTheme): ColorScheme {
  return COLOR_THEMES[theme];
}

// Helper function to get border color for each theme
export function getBorderColor(theme: ColorTheme): string | ((text: string) => string) {
  switch (theme) {
    case 'blue':
      return chalk.hex('#2563eb'); // Blue-600
    case 'green':
      return chalk.hex('#16a34a'); // Green-600
    case 'orange':
      return chalk.hex('#ea580c'); // Orange-600
    case 'purple':
      return chalk.hex('#7c3aed'); // Violet-600
    case 'classic':
    default:
      return 'cyan'; // Keep classic cyan for classic theme
  }
}
