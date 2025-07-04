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
  
  // Fix relative imports: add .js extension
  const fixedContent = content
    // Fix relative imports without extensions (starting with ./ or ../)
    .replace(/from ['"](\\.{1,2}\/[^'"]*[^'"\/])['"];/g, "from '$1.js';")
    // Fix relative imports from directory paths (add /index.js)
    .replace(/from ['"](\\.{1,2}\/[^'"]*\/)['"];/g, "from '$1index.js';")
    // Fix absolute-style imports that should be relative (starting with ../)
    .replace(/from ['"](\.\.\/[^'"]*[^'"\/])['"];/g, "from '$1.js';")
    // Fix double extensions
    .replace(/\.js\.js/g, '.js');

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