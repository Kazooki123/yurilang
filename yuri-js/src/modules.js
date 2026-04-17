import { readFileSync, existsSync } from 'node:fs';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { parse } from './parser.js';

const __dirname = dirname(fileURLToPath(import.meta.url));
const STORE_PATH = join(__dirname, '..', '..', 'store');

const loadedModules = new Set();

function normalize(name) {
  return name.replaceAll('_', '').toLowerCase();
}

function extractFunctions(node, functions) {
  if (node.type === 'function') {
    const [name, params] = node.value;
    functions.set(name, [params, node.children]);
  }

  for (const child of node.children) {
    extractFunctions(child, functions);
  }
}

export function loadModule(name, functions) {
  const normalized = normalize(name);
  if (loadedModules.has(normalized)) return;
  const filename = join(STORE_PATH, `${normalized}.yuri`);

  if (!existsSync(filename)) {
    throw new Error(`Module '${name}' not found at ${filename}`);
  }

  const code = readFileSync(filename, 'utf-8');
  const tree = parse(code);

  extractFunctions(tree, functions);
  loadedModules.add(normalized);
}
