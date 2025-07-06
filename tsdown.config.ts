import { defineConfig } from 'tsdown';

export default defineConfig({
  entry: ['./src/cli/index.ts'],
  outDir: 'dist',
  platform: 'node',
  format: ['es'],
  dts: true,
  shims: true,
  clean: true,
});
