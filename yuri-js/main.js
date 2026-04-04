import { readFileSync } from 'node:fs';
import { run } from './src/interpreter.js';
import { repl } from './src/repl.js';

const [file] = process.argv.slice(2);

if (!file) repl(); else try {
  run(readFileSync(file, 'utf-8'));
} catch (e) {
  console.log(e.code === 'ENOENT' ? `File not found: ${file}` : e.message);
}
