// A working gta6-meme-x-01 entry (Node 22, standard library only).
//
// The work is the post: the meme picture made in art/, posted publicly on X from
// a public account, its text carrying make.fun and the entrant's play code. This
// program hands the post's address to the gate, and nothing more: the house reads
// the post from X itself (its first picture and its text) and writes the dossier
// the judge sees, in place of anything this program writes about it.
//
// What it does beyond the starter's copy:
//   - refuses a POST.json that still holds the placeholder or is not an
//     x.com/twitter.com status address, so a stale build cannot be submitted;
//   - normalises the address to the canonical https://x.com/<handle>/status/<id>
//     form the gate parses, and drops tracking query strings;
//   - checks the meme picture it ships is really a picture (PNG/JPEG/WebP magic
//     bytes, not a GIF or a video), because the judge's first look is that picture;
//   - copies both through with a receipt line, so a local run shows what it did.
//
// Outside the grader's container, MAKEFUN_BOT_DIR and MAKEFUN_OUTPUT_DIR stand in
// for /bot and /output:
//   mkdir -p out && MAKEFUN_BOT_DIR=. MAKEFUN_OUTPUT_DIR=out node main.ts

import { copyFileSync, existsSync, mkdirSync, readFileSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';

const BOT_DIR = process.env.MAKEFUN_BOT_DIR ?? '/bot';
const OUTPUT_DIR = process.env.MAKEFUN_OUTPUT_DIR ?? '/output';

interface PostRecord {
  url: string;
}

/** Canonical post address, or an error string explaining why it cannot be used. */
function canonicalPostUrl(raw: unknown): string {
  if (typeof raw !== 'string' || raw.trim() === '') {
    return 'POST.json holds no url';
  }
  let parsed: URL;
  try {
    parsed = new URL(raw.trim());
  } catch {
    return `POST.json url is not a URL: ${raw}`;
  }
  const host = parsed.hostname.replace(/^www\./, '').toLowerCase();
  if (host !== 'x.com' && host !== 'twitter.com' && host !== 'mobile.x.com') {
    return `POST.json url is not an X post (host ${host})`;
  }
  // /<handle>/status/<digits>, optionally followed by /photo/1 and a query
  const match = parsed.pathname.match(/^\/([A-Za-z0-9_]{1,15})\/status(?:es)?\/(\d+)/);
  if (!match) {
    return `POST.json url is not a status address: ${parsed.pathname}`;
  }
  const [, handle, id] = match;
  if (id.length < 15) {
    return `POST.json post id looks too short (${id}), the placeholder has not been replaced`;
  }
  return `https://x.com/${handle}/status/${id}`;
}

/** True when the file's first bytes are a picture the house accepts (not a GIF, not a video). */
function looksLikePicture(path: string): true | string {
  const head = readFileSync(path).subarray(0, 16);
  const isPng = head[0] === 0x89 && head.toString('latin1', 1, 4) === 'PNG';
  const isJpeg = head[0] === 0xff && head[1] === 0xd8 && head[2] === 0xff;
  const isWebp = head.toString('latin1', 0, 4) === 'RIFF' && head.toString('latin1', 8, 12) === 'WEBP';
  if (isPng || isJpeg || isWebp) return true;
  if (head.toString('latin1', 0, 3) === 'GIF') return 'the meme is a GIF, which the house refuses';
  return 'the meme is not a PNG, JPEG or WebP picture';
}

function main(): void {
  mkdirSync(OUTPUT_DIR, { recursive: true });

  const postPath = join(BOT_DIR, 'POST.json');
  let record: PostRecord;
  try {
    record = JSON.parse(readFileSync(postPath, 'utf8')) as PostRecord;
  } catch (err) {
    console.error(`POST.json could not be read from ${BOT_DIR}: ${(err as Error).message}`);
    process.exit(1);
  }

  const url = canonicalPostUrl(record.url);
  if (!url.startsWith('https://x.com/')) {
    console.error(`refusing to submit: ${url}`);
    process.exit(1);
  }

  writeFileSync(join(OUTPUT_DIR, 'POST.json'), `${JSON.stringify({ url }, null, 2)}\n`);
  copyFileSync(postPath, join(OUTPUT_DIR, 'POST.source.json'));

  // The picture rides along so the grader's output carries what the post showed.
  const picture = join(BOT_DIR, 'art', 'meme.png');
  let shippedPicture = false;
  if (existsSync(picture)) {
    const verdict = looksLikePicture(picture);
    if (verdict !== true) {
      console.error(`refusing to submit: ${verdict}`);
      process.exit(1);
    }
    copyFileSync(picture, join(OUTPUT_DIR, 'meme.png'));
    shippedPicture = true;
  }

  console.log(`post ${url}`);
  console.log(`wrote ${join(OUTPUT_DIR, 'POST.json')}`);
  if (shippedPicture) {
    console.log(`shipped ${join(OUTPUT_DIR, 'meme.png')}`);
  } else {
    console.log('note: no art/meme.png present, nothing shipped beside the post');
  }
}

main();
