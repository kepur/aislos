import { readFileSync, readdirSync, statSync } from "node:fs";
import { join } from "node:path";

const root = new URL("..", import.meta.url).pathname;

const sharedNeedles = [
  "/auth/login",
  "/auth/register",
  "/auth/me",
  "/auth/system-mode",
  "/marketplace/filters",
  "/marketplace/feed",
  "/marketplace/items/",
  "/addresses",
  "/intents",
  "/intents/my",
  "/offers/",
  "/award",
  "/withdraw",
  "/orders",
  "/orders/my",
  "/accept",
  "/delivery",
  "/dispute",
  "/supplier/intents/matching",
  "/supplier/offers",
  "/supplier/catalog/items",
  "/supplier-candidates",
  "/bind",
  "/wallets/me",
  "/wallets/transactions",
  "/wallets/deposits",
  "/submit-tx",
  "/notifications/my",
  "/notifications/",
  "/notifications/read-all",
  "/threads/order/",
  "/messages",
];

function collectFiles(dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    if (["node_modules", ".nuxt", ".output", "dist"].includes(name)) continue;
    const path = join(dir, name);
    const stat = statSync(path);
    if (stat.isDirectory()) out.push(...collectFiles(path));
    else if (/\.(vue|ts)$/.test(name)) out.push(path);
  }
  return out;
}

function readFrontend(name) {
  return collectFiles(join(root, name))
    .map((file) => readFileSync(file, "utf8"))
    .join("\n");
}

const pc = readFrontend("pc-frontend");
const h5 = readFrontend("h5-frontend");
const missing = [];

for (const needle of sharedNeedles) {
  if (!pc.includes(needle)) missing.push(`pc-frontend missing ${needle}`);
  if (!h5.includes(needle)) missing.push(`h5-frontend missing ${needle}`);
}

if (missing.length) {
  console.error("Frontend API parity check failed:");
  for (const line of missing) console.error(`- ${line}`);
  process.exit(1);
}

console.log(`Frontend API parity check passed (${sharedNeedles.length} shared API fragments).`);
