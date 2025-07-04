import { getColorScheme, COLOR_THEMES, ColorTheme } from './colorThemes';

describe('Color Themes', () => {
  describe('COLOR_THEMES', () => {
    it('should have the correct number of themes', () => {
      expect(Object.keys(COLOR_THEMES)).toHaveLength(8);
    });

    it('should have exactly 5 colors in each theme except random', () => {
      const themes = Object.entries(COLOR_THEMES);
      themes.forEach(([key, theme]) => {
        if (key !== 'random') {
          expect(theme.colors).toHaveLength(5);
        }
      });
    });

    it('should have monochrome themes with string colors', () => {
      const monochromeThemes = ['blue', 'green', 'red', 'purple', 'yellow', 'cyan'] as ColorTheme[];
      monochromeThemes.forEach(themeKey => {
        const theme = COLOR_THEMES[themeKey];
        expect(theme.name).toContain('Monochrome');
        theme.colors.forEach(color => {
          expect(typeof color).toBe('string');
        });
      });
    });
  });

  describe('getColorScheme', () => {
    it('should return monochrome theme for blue', () => {
      const scheme = getColorScheme('blue');
      expect(scheme.name).toBe('Blue (Monochrome)');
      expect(scheme.colors).toHaveLength(5);
      scheme.colors.forEach(color => {
        expect(typeof color).toBe('string');
      });
    });

    it('should return monochrome theme for green', () => {
      const scheme = getColorScheme('green');
      expect(scheme.name).toBe('Green (Monochrome)');
      expect(scheme.colors).toHaveLength(5);
      scheme.colors.forEach(color => {
        expect(typeof color).toBe('string');
      });
    });

    it('should return monochrome theme for all new themes', () => {
      const monochromeThemes = ['red', 'purple', 'yellow', 'cyan'] as ColorTheme[];
      monochromeThemes.forEach(themeKey => {
        const scheme = getColorScheme(themeKey);
        expect(scheme.name).toContain('Monochrome');
        expect(scheme.colors).toHaveLength(5);
        scheme.colors.forEach(color => {
          expect(typeof color).toBe('string');
        });
      });
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
    });

    it('should return one of the available themes when random is selected', () => {
      const possibleThemes = ['blue', 'green', 'red', 'purple', 'yellow', 'cyan', 'classic'] as ColorTheme[];
      
      // Test multiple times to ensure randomness works
      for (let i = 0; i < 10; i++) {
        const randomScheme = getColorScheme('random');
        const isValidTheme = possibleThemes.some(
          themeKey => COLOR_THEMES[themeKey].name === randomScheme.name
        );
        expect(isValidTheme).toBe(true);
      }
    });

    it('should contain valid terminal colors in monochrome themes', () => {
      const scheme = getColorScheme('blue');
      scheme.colors.forEach(color => {
        expect(typeof color).toBe('string');
        // All colors should be standard terminal color names
        expect(color).toMatch(/^(gray|blue|blueBright|green|greenBright|red|redBright|magenta|magentaBright|yellow|yellowBright|cyan|cyanBright)$/);
      });
    });
  });
});