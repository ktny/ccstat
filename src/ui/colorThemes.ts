export type ColorTheme = 'blue' | 'green' | 'red' | 'purple' | 'yellow' | 'cyan' | 'classic' | 'random';

export interface ColorScheme {
  name: string;
  colors: string[];
}

// Helper function to create gradients using standard terminal colors with same base hue
const createTerminalGradient = (baseColors: string[], name: string): ColorScheme => ({
  name: `${name} (Monochrome)`,
  colors: baseColors,
});

export const COLOR_THEMES: Record<ColorTheme, ColorScheme> = {
  blue: createTerminalGradient([
    'gray',         // Neutral base
    'blue',         // Light blue
    'blue',         // Medium blue (same as light for terminal limitation)
    'blueBright',   // Bright blue
    'blue',         // Dark blue (using regular blue)
  ], 'Blue'),
  
  green: createTerminalGradient([
    'gray',          // Neutral base
    'green',         // Light green
    'green',         // Medium green
    'greenBright',   // Bright green
    'green',         // Dark green
  ], 'Green'),
  
  red: createTerminalGradient([
    'gray',        // Neutral base
    'red',         // Light red
    'red',         // Medium red
    'redBright',   // Bright red
    'red',         // Dark red
  ], 'Red'),
  
  purple: createTerminalGradient([
    'gray',           // Neutral base
    'magenta',        // Light purple/magenta
    'magenta',        // Medium purple
    'magentaBright',  // Bright purple
    'magenta',        // Dark purple
  ], 'Purple'),
  
  yellow: createTerminalGradient([
    'gray',           // Neutral base
    'yellow',         // Light yellow
    'yellow',         // Medium yellow  
    'yellowBright',   // Bright yellow
    'yellow',         // Dark yellow
  ], 'Yellow'),
  
  cyan: createTerminalGradient([
    'gray',         // Neutral base
    'cyan',         // Light cyan
    'cyan',         // Medium cyan
    'cyanBright',   // Bright cyan
    'cyan',         // Dark cyan
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