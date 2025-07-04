import chalk from 'chalk';

export type ColorTheme = 'blue' | 'green' | 'red' | 'purple' | 'classic' | 'random';

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
  
  red: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#fecaca',  // Red-200 (very light red)
    '#f87171',  // Red-400 (medium red)
    '#dc2626',  // Red-600 (bright red)
    '#991b1b',  // Red-800 (very dark red)
  ], 'Red'),
  
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
  
  random: {
    name: 'Random',
    colors: [], // Will be selected randomly
  },
};

const THEME_KEYS = Object.keys(COLOR_THEMES).filter(key => key !== 'random') as ColorTheme[];

export function getColorScheme(theme: ColorTheme): ColorScheme {
  if (theme === 'random') {
    const randomTheme = THEME_KEYS[Math.floor(Math.random() * THEME_KEYS.length)];
    return COLOR_THEMES[randomTheme];
  }
  return COLOR_THEMES[theme];
}