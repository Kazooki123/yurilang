import { run } from './interpreter.js';
import { stdin, stdout } from 'node:process';
import { createInterface } from 'node:readline/promises';

const COLORS = [
  '\x1b[38;5;166m', // dark orange
  '\x1b[38;5;208m', // orange
  '\x1b[38;5;223m', // cream
  '\x1b[38;5;212m', // pink
  '\x1b[38;5;197m' // dark pink
];
const RESET = '\x1b[0m';

const BANNER = [
  '██╗   ██╗██╗   ██╗██████╗ ██╗',
  '╚██╗ ██╔╝██║   ██║██╔══██╗██║',
  ' ╚████╔╝ ██║   ██║██████╔╝██║',
  '  ╚██╔╝  ██║   ██║██╔══██╗██║',
  '   ██║   ╚██████╔╝██║  ██║██║',
  '   ╚═╝    ╚═════╝ ╚═╝  ╚═╝╚═╝'
];

function printBanner() {
  for (let i = 0; i < BANNER.length; i++) {
    const color = COLORS[Math.floor((i * COLORS.length) / BANNER.length)];
    console.log(color + BANNER[i] + RESET);
  }
  console.log('🧡 YuriLang REPL 🩷\n');
}

function shoutouts() {
  console.log('Shout Outs!!');

  const names = ['@jamiw (1024ping)', '@gseppo', '@lunalapigeonne', '@anormalwintrovert', '@hexagonos', '@theophilus_dev'];

  for (let i = 0; i < names.length; i += 2) {
    const left = names[i].padEnd(30);
    const right = names[i + 1] ?? '';
    console.log(`   ${left} ${right}`);
  }

  console.log();
}

export async function repl() {
  printBanner();
  console.log('Made with Love by StarloExoliz! (js port)');

  shoutouts();
  console.log("YuriLang REPL 💖 (type 'exit' to quit)\n");

  const rl = createInterface({
    input: stdin,
    output: stdout,
    prompt: '>>> '
  });

  rl.prompt();

  for await (const code of rl) {
    const trimmed = code.trim();

    if (trimmed === 'exit' || trimmed === 'quit') {
      console.log('bye bye! :<');
      break;
    }

    try {
      run(trimmed);
    } catch (err) {
      console.log('Error:', err.message);
    }

    rl.prompt();
  }

  rl.close();
}
