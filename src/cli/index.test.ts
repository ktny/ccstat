import { Command } from 'commander';

describe('CLI options after removing debug and worktree', () => {
  let program: Command;

  beforeEach(() => {
    program = new Command();
    program
      .name('ccstat')
      .description('Analyze Claude Code session history and visualize project activity patterns')
      .version('1.0.0')
      .option('-d, --days <number>', 'display activity for the last N days', '1')
      .option('-H, --hours <number>', 'display activity for the last N hours')
      .option('--color <theme>', 'color theme: blue, green, orange, purple, classic', 'green')
      .option(
        '--sort <field>',
        'sort by field: project, timeline, events, duration (default: timeline)',
        'timeline'
      )
      .option('--reverse', 'reverse sort order (default: ascending)')
      .option('--all-time', 'display all session history across all time periods')
      .option('-p, --project <names...>', 'filter by project names (space-separated)');
  });

  it('should not have --debug option', () => {
    const helpText = program.helpInformation();
    expect(helpText).not.toContain('--debug');
    expect(helpText).not.toContain('enable debug output');
  });

  it('should not have --worktree option', () => {
    const helpText = program.helpInformation();
    expect(helpText).not.toContain('--worktree');
    expect(helpText).not.toContain('display directories separately');
  });

  it('should still have other essential options', () => {
    const helpText = program.helpInformation();
    expect(helpText).toContain('--days');
    expect(helpText).toContain('--hours');
    expect(helpText).toContain('--color');
    expect(helpText).toContain('--sort');
  });

  it('should have --project option', () => {
    const helpText = program.helpInformation();
    expect(helpText).toContain('-p, --project');
    expect(helpText).toContain('filter by project names');
    expect(helpText).toContain('space-separated');
  });

  it('should parse options without debug or worktree', () => {
    program.parse(['node', 'ccstat', '--days', '3', '--color', 'blue']);
    const options = program.opts();

    expect(options.days).toBe('3');
    expect(options.color).toBe('blue');
    expect(options.debug).toBeUndefined();
    expect(options.worktree).toBeUndefined();
  });

  it('should parse single project option', () => {
    program.parse(['node', 'ccstat', '-p', 'myproject']);
    const options = program.opts();

    expect(options.project).toEqual(['myproject']);
  });

  it('should parse multiple project options (space-separated)', () => {
    program.parse(['node', 'ccstat', '--project', 'project1', 'project2', 'project3']);
    const options = program.opts();

    expect(options.project).toEqual(['project1', 'project2', 'project3']);
  });

  it('should handle empty project option', () => {
    program.parse(['node', 'ccstat', '--days', '3']);
    const options = program.opts();

    expect(options.project).toBeUndefined();
  });
});
