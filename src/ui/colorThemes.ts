export type ColorTheme = 'blue' | 'green' | 'red' | 'purple' | 'classic' | 'random';

export interface ColorScheme {
  name: string;
  colors: string[];
}

export const COLOR_THEMES: Record<ColorTheme, ColorScheme> = {
  blue: {
    name: 'Blue (Cool Gradient)',
    colors: ['gray', 'blue', 'blueBright', 'cyan', 'cyanBright'],
  },
  green: {
    name: 'Green (Nature Gradient)',
    colors: ['gray', 'green', 'greenBright', 'yellow', 'yellowBright'],
  },
  red: {
    name: 'Red (Warm Gradient)',
    colors: ['gray', 'magenta', 'red', 'redBright', 'yellow'],
  },
  purple: {
    name: 'Purple (Mystic Gradient)',
    colors: ['gray', 'magenta', 'magentaBright', 'blue', 'blueBright'],
  },
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