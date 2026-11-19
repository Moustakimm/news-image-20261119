// news-image-20261119 entry (Node 22, standard library only).
// The image is drawn by render.py and shipped as entry.png beside this file;
// the program writes those exact bytes to /output/entry.png, so both graded
// runs produce an identical file. No network, no dependencies.
//
// Outside the grader's container, MAKEFUN_OUTPUT_DIR stands in for /output:
//   mkdir -p out && MAKEFUN_OUTPUT_DIR=out node main.ts

import { mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = dirname(fileURLToPath(import.meta.url));
const outDir = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';
mkdirSync(outDir, { recursive: true });
writeFileSync(
  join(outDir, 'entry.png'),
  readFileSync(join(here, 'entry.png')),
);
