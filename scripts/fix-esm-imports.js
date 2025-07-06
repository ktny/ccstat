#!/usr/bin/env node

/**
 * Fix ESM import paths in built JavaScript files
 * This script adds .js extensions to relative imports for proper ESM resolution
 */

import { readdir, readFile, writeFile } from 'fs/promises';
import { join, extname } from 'path';

const DIST_DIR = 'dist';

async function findJSFiles(dir) {
  const files = [];
  const items = await readdir(dir, { withFileTypes: true });

  for (const item of items) {
    const fullPath = join(dir, item.name);
    if (item.isDirectory()) {
      files.push(...(await findJSFiles(fullPath)));
    } else if (extname(item.name) === '.js') {
      files.push(fullPath);
    }
  }

  return files;
}

async function fixImportsInFile(filePath) {
  const content = await readFile(filePath, 'utf-8');
  let fixedContent = content;

  // 1. First pass: Add .js extensions to relative imports
  fixedContent = fixedContent
    .replace(/from ['"](\\.\/[^'"]*[^'"\/\.])['"];/g, "from '$1.js';")
    .replace(/from ['"](\.\.\/[^'"]*[^'"\/\.])['"];/g, "from '$1.js';");

  // 2. Fix directory imports to use index.js
  fixedContent = fixedContent
    .replace(/from ['"](\\.{1,2}\/[^'"]*\/)['"];/g, "from '$1index.js';");

  // 3. Fix specific known import issues
  fixedContent = fixedContent
    // core/parser directory import
    .replace(/from ['"]\.\.\/core\/parser['"];/g, "from '../core/parser/index.js';")
    .replace(/from ['"]\.\.\/core\/git['"];/g, "from '../core/git/index.js';")
    // ui components without .js
    .replace(/from ['"]\.\.\/ui\/([^'"\/]+)['"];/g, "from '../ui/$1.js';")
    .replace(/from ['"]\.\/([^'"\/]+)['"];/g, "from './$1.js';");

  // 4. Special fix for dist/index.js: convert ../ to ./
  if (filePath.endsWith('dist/index.js') || filePath.endsWith('dist\\index.js')) {
    fixedContent = fixedContent
      .replace(/from ['"]\.\.\/ui\//g, "from './ui/")
      .replace(/from ['"]\.\.\/core\//g, "from './core/")
      .replace(/from ['"]\.\.\/models\//g, "from './models/")
      .replace(/from ['"]\.\.\/utils\//g, "from './utils/");
  }

  // 5. Clean up double extensions
  fixedContent = fixedContent.replace(/\.js\.js/g, '.js');

  if (content !== fixedContent) {
    await writeFile(filePath, fixedContent, 'utf-8');
    console.log(`Fixed imports in: ${filePath}`);
  }
}

async function main() {
  try {
    console.log('🔧 Fixing ESM imports in built files...');
    
    const jsFiles = await findJSFiles(DIST_DIR);
    
    for (const file of jsFiles) {
      await fixImportsInFile(file);
    }
    
    console.log(`✅ Processed ${jsFiles.length} files`);
  } catch (error) {
    console.error('❌ Error fixing imports:', error);
    process.exit(1);
  }
}

main();