/**
 * fetch_vvv_tweets.mjs
 *
 * Fetches recent tweets from @VVVStockAnalyst via Rettiwt-API and filters
 * for trade mentions of MTAR, Ather, Hitachi, NALCO, BSE, MCX, Avanti, Gallantt.
 *
 * SETUP (one-time):
 *   1. Install the browser extension from README below
 *   2. Log into X/Twitter in incognito mode
 *   3. Click "Get Key" → copy the RETTIWT_API_KEY
 *   4. Add to .env:  RETTIWT_API_KEY=<your_key>
 *
 *   Extension links:
 *     Chrome: https://chromewebstore.google.com/detail/x-auth-helper/igpkhkjmpdecacocghpgkghdcmcmpfhp
 *     Firefox: https://addons.mozilla.org/en-US/firefox/addon/rettiwt-auth-helper
 *
 * Usage:
 *   node fetch_vvv_tweets.mjs                  # last 3 pages, stock matches only
 *   node fetch_vvv_tweets.mjs --pages 10       # fetch more pages
 *   node fetch_vvv_tweets.mjs --all            # print every tweet (no filter)
 *   RETTIWT_API_KEY=xyz node fetch_vvv_tweets.mjs
 */

import { Rettiwt } from 'rettiwt-api';
import { readFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dir = dirname(fileURLToPath(import.meta.url));

// ── Load .env manually (no dependency on dotenv) ──────────────────────────────
function loadEnv() {
  try {
    const envPath = resolve(__dir, '.env');
    const lines = readFileSync(envPath, 'utf8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const eqIdx = trimmed.indexOf('=');
      if (eqIdx === -1) continue;
      const key = trimmed.slice(0, eqIdx).trim();
      const val = trimmed.slice(eqIdx + 1).trim();
      if (!process.env[key]) process.env[key] = val;
    }
  } catch {
    // .env not found — rely on process.env directly
  }
}
loadEnv();

const API_KEY = process.env.RETTIWT_API_KEY ?? '';

const HANDLE = 'VVVStockAnalyst';

// ── Stock keyword map ─────────────────────────────────────────────────────────
const STOCK_KEYWORDS = [
  { key: 'MTAR',     patterns: ['mtar'] },
  { key: 'ATHER',    patterns: ['ather energy', 'ather '] },
  { key: 'HITACHI',  patterns: ['hitachi', 'powerindia'] },
  { key: 'NALCO',    patterns: ['nalco', 'national alum', 'nationalalum'] },
  { key: 'BSE',      patterns: ['bse '] },
  { key: 'MCX',      patterns: [' mcx', 'mcx '] },
  { key: 'AVANTI',   patterns: ['avanti'] },
  { key: 'GALLANTT', patterns: ['gallantt'] },
];

const TRADE_WORDS = [
  'buy', 'bought', 'entry', 'entered', 'added', 'sold', 'exit', 'exited',
  'booked', 'profit', 'loss', 'stop', '5dma', 'below 5', 'above 5',
  'gains', 'trailing', '%', 'lacs', 'lakhs',
];

function matchesStock(text) {
  const lower = text.toLowerCase();
  for (const stock of STOCK_KEYWORDS) {
    for (const pat of stock.patterns) {
      if (lower.includes(pat)) return stock.key;
    }
  }
  return null;
}

function isTradeRelated(text) {
  const lower = text.toLowerCase();
  return TRADE_WORDS.some(w => lower.includes(w));
}

function formatDate(dateStr) {
  if (!dateStr) return '—';
  return new Date(dateStr).toLocaleString('en-IN', {
    day: '2-digit', month: 'short', year: 'numeric',
    hour: '2-digit', minute: '2-digit', timeZone: 'Asia/Kolkata',
  });
}

// ── Main ──────────────────────────────────────────────────────────────────────
async function main(pages = 3, printAll = false) {
  if (!API_KEY) {
    console.error(`
╔══════════════════════════════════════════════════════════════════╗
║  RETTIWT_API_KEY not set — user authentication required          ║
║                                                                  ║
║  X/Twitter now blocks all unauthenticated (guest) requests.      ║
║  You need a one-time API key from your own Twitter account.      ║
║                                                                  ║
║  HOW TO GET YOUR KEY (2 minutes):                                ║
║  1. Install browser extension:                                   ║
║     Chrome:  https://chromewebstore.google.com/detail/           ║
║              x-auth-helper/igpkhkjmpdecacocghpgkghdcmcmpfhp     ║
║     Firefox: https://addons.mozilla.org/en-US/firefox/           ║
║              addon/rettiwt-auth-helper                           ║
║  2. Open incognito / private window, go to x.com, log in         ║
║  3. Click the extension → "Get Key" → copy the key               ║
║  4. Add to your .env file:                                       ║
║        RETTIWT_API_KEY=<paste_key_here>                          ║
║  5. Re-run:  node fetch_vvv_tweets.mjs                           ║
║                                                                  ║
║  The key lasts ~5 years (tied to your session cookie).           ║
╚══════════════════════════════════════════════════════════════════╝
`);
    process.exit(1);
  }

  const rettiwt = new Rettiwt({ apiKey: API_KEY });

  console.log(`\nFetching @${HANDLE} timeline (${pages} page(s))...\n`);

  // Resolve user ID
  let userId;
  try {
    const user = await rettiwt.user.details(HANDLE);
    userId = user?.id;
    console.log(`✓ User: ${user?.fullName} (@${user?.userName})  ID: ${userId}`);
    console.log(`  Followers: ${user?.followersCount?.toLocaleString()}\n`);
  } catch (err) {
    console.error(`Failed to fetch user: ${err.message}`);
    process.exit(1);
  }

  // Paginate timeline
  let allTweets = [];
  let cursor;
  for (let p = 0; p < pages; p++) {
    try {
      const result = await rettiwt.user.timeline(userId, 20, cursor);
      const tweets = result?.list ?? [];
      if (!tweets.length) { console.log(`Page ${p + 1}: no more tweets.`); break; }
      allTweets.push(...tweets);
      cursor = result?.next?.value;
      console.log(`Page ${p + 1}: +${tweets.length} tweets  (total ${allTweets.length})`);
      if (!cursor) break;
      await new Promise(r => setTimeout(r, 1500));
    } catch (err) {
      console.error(`Page ${p + 1} error: ${err.message}`);
      break;
    }
  }

  if (!allTweets.length) { console.log('\nNo tweets fetched.'); return; }

  allTweets.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));

  // Categorise
  const matched = [];
  const all = [];
  for (const t of allTweets) {
    const text  = t.fullText ?? t.text ?? '';
    const date  = formatDate(t.createdAt);
    const url   = `https://x.com/${HANDLE}/status/${t.id}`;
    const stock = matchesStock(text);
    const trade = isTradeRelated(text);
    all.push({ date, stock: stock ?? '—', trade, text: text.replace(/\n/g, ' '), url });
    if (stock) matched.push({ date, stock, trade, text: text.replace(/\n/g, ' '), url });
  }

  const target = printAll ? all : matched;

  console.log('\n' + '═'.repeat(90));
  console.log(printAll
    ? `ALL TWEETS (${all.length})`
    : `STOCK MATCHES: ${matched.length} / ${allTweets.length} tweets  |  date range: ${all.at(-1)?.date} → ${all[0]?.date}`
  );
  console.log('═'.repeat(90));

  if (!target.length) {
    console.log('\nNo stock mentions found. Try --pages 10 to go further back.');
    return;
  }

  // Group by stock
  const groups = {};
  for (const t of target) {
    const k = t.stock ?? '—';
    (groups[k] ??= []).push(t);
  }

  for (const [stock, tweets] of Object.entries(groups)) {
    console.log(`\n── ${stock} (${tweets.length} tweet${tweets.length > 1 ? 's' : ''}) ${'─'.repeat(60)}`);
    for (const t of tweets) {
      const flag = t.trade ? '  ← TRADE SIGNAL' : '';
      console.log(`  📅 ${t.date}${flag}`);
      console.log(`  ${t.text.slice(0, 300)}`);
      console.log(`  🔗 ${t.url}\n`);
    }
  }

  console.log('═'.repeat(90) + '\n');
}

// CLI args
const args = process.argv.slice(2);
const pages = args.includes('--pages')
  ? parseInt(args[args.indexOf('--pages') + 1], 10)
  : 3;
const printAll = args.includes('--all');

main(pages, printAll).catch(err => {
  console.error('Fatal:', err.message);
  process.exit(1);
});
