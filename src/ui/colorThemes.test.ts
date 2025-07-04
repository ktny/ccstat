import { getColorScheme, COLOR_THEMES, ColorTheme } from './colorThemes';

describe('Color Themes', () => {
  describe('COLOR_THEMES', () => {
    it('should have the correct number of themes', () => {
      expect(Object.keys(COLOR_THEMES)).toHaveLength(6);
    });

    it('should have exactly 5 colors in each theme except random', () => {
      const themes = Object.entries(COLOR_THEMES);
      themes.forEach(([key, theme]) => {
        if (key !== 'random') {
          expect(theme.colors).toHaveLength(5);
        }
      });
    });

    it('should include gray as the first color in all non-random themes', () => {
      const themes = Object.entries(COLOR_THEMES);
      themes.forEach(([key, theme]) => {
        if (key !== 'random') {
          expect(theme.colors[0]).toBe('gray');
        }
      });
    });
  });

  describe('getColorScheme', () => {
    it('should return the correct color scheme for blue theme', () => {
      const scheme = getColorScheme('blue');
      expect(scheme.name).toBe('Blue (Cool Gradient)');
      expect(scheme.colors).toEqual(['gray', 'blue', 'blueBright', 'cyan', 'cyanBright']);
    });

    it('should return the correct color scheme for green theme', () => {
      const scheme = getColorScheme('green');
      expect(scheme.name).toBe('Green (Nature Gradient)');
      expect(scheme.colors).toEqual(['gray', 'green', 'greenBright', 'yellow', 'yellowBright']);
    });

    it('should return the correct color scheme for red theme', () => {
      const scheme = getColorScheme('red');
      expect(scheme.name).toBe('Red (Warm Gradient)');
      expect(scheme.colors).toEqual(['gray', 'magenta', 'red', 'redBright', 'yellow']);
    });

    it('should return the correct color scheme for purple theme', () => {
      const scheme = getColorScheme('purple');
      expect(scheme.name).toBe('Purple (Mystic Gradient)');
      expect(scheme.colors).toEqual(['gray', 'magenta', 'magentaBright', 'blue', 'blueBright']);
    });

    it('should return the correct color scheme for classic theme', () => {
      const scheme = getColorScheme('classic');
      expect(scheme.name).toBe('Classic (GitHub Style)');
      expect(scheme.colors).toEqual(['gray', 'green', 'greenBright', 'yellow', 'red']);
    });

    it('should return a random non-random theme when random is selected', () => {
      const scheme = getColorScheme('random');
      expect(scheme.name).not.toBe('Random');
      expect(scheme.colors).toHaveLength(5);
      expect(scheme.colors[0]).toBe('gray');
    });

    it('should return one of the available themes when random is selected', () => {
      const possibleThemes = ['blue', 'green', 'red', 'purple', 'classic'] as ColorTheme[];
      const schemes = possibleThemes.map(theme => COLOR_THEMES[theme]);
      
      // Test multiple times to ensure randomness works
      for (let i = 0; i < 10; i++) {
        const randomScheme = getColorScheme('random');
        const isValidTheme = schemes.some(
          scheme => scheme.name === randomScheme.name && 
          JSON.stringify(scheme.colors) === JSON.stringify(randomScheme.colors)
        );
        expect(isValidTheme).toBe(true);
      }
    });
  });
});