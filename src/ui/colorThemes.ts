import chalk from 'chalk';

export type ColorTheme = 'blue' | 'green' | 'red' | 'purple' | 'yellow' | 'cyan' | 'classic' | 'random';

export interface ColorScheme {
  name: string;
  colors: (string | ((text: string) => string))[];
}

// Helper function to create hex color gradients for same hue with different saturation/lightness
const createHexGradient = (hexColors: string[], name: string): ColorScheme => ({
  name: `${name} (Gradient)`,
  colors: hexColors.map(color => (text: string) => chalk.hex(color)(text)),
});

export const COLOR_THEMES: Record<ColorTheme, ColorScheme> = {
  blue: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#93c5fd',  // Blue-300 (light blue, low saturation)
    '#60a5fa',  // Blue-400 (medium blue)
    '#3b82f6',  // Blue-500 (bright blue)
    '#1d4ed8',  // Blue-700 (dark blue, high saturation)
  ], 'Blue'),
  
  green: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#86efac',  // Green-300 (light green, low saturation)
    '#4ade80',  // Green-400 (medium green)
    '#22c55e',  // Green-500 (bright green)
    '#15803d',  // Green-700 (dark green, high saturation)
  ], 'Green'),
  
  red: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#fca5a5',  // Red-300 (light red, low saturation)
    '#f87171',  // Red-400 (medium red)
    '#ef4444',  // Red-500 (bright red)
    '#dc2626',  // Red-600 (dark red, high saturation)
  ], 'Red'),
  
  purple: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#c4b5fd',  // Violet-300 (light purple, low saturation)
    '#a78bfa',  // Violet-400 (medium purple)
    '#8b5cf6',  // Violet-500 (bright purple)
    '#7c3aed',  // Violet-600 (dark purple, high saturation)
  ], 'Purple'),
  
  yellow: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#fde047',  // Yellow-300 (light yellow, low saturation)
    '#facc15',  // Yellow-400 (medium yellow)
    '#eab308',  // Yellow-500 (bright yellow)
    '#ca8a04',  // Yellow-600 (dark yellow, high saturation)
  ], 'Yellow'),
  
  cyan: createHexGradient([
    '#9ca3af',  // Gray-400 (neutral base)
    '#67e8f9',  // Cyan-300 (light cyan, low saturation)
    '#22d3ee',  // Cyan-400 (medium cyan)
    '#06b6d4',  // Cyan-500 (bright cyan)
    '#0891b2',  // Cyan-600 (dark cyan, high saturation)
  ], 'Cyan'),
  
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