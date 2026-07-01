import { getCollection, type CollectionEntry } from 'astro:content';
import type { NotebookStatus } from '../config/status';

export const UNCOLLECTED = '__uncollected';

// Display-name overrides for collections whose slug doesn't capitalize cleanly.
// The slug (used in URLs) stays as-is; only the shown label changes.
const COLLECTION_LABELS: Record<string, string> = {
  mujoco: 'Example: Mujoco',
  'neuron-models': 'Example: Neuron models',
  streamlit: 'Example: Streamlit',
};

export function collectionLabel(name: string): string {
  if (name === UNCOLLECTED) return 'Misc';
  return COLLECTION_LABELS[name] ?? name.charAt(0).toUpperCase() + name.slice(1).replace(/-/g, ' ');
}

export type Entry = {
  id: string;
  title: string;
  date: Date;
  collection: string | null;
  status: NotebookStatus | null;
  order: number | null;
  kind: 'articles' | 'notebooks';
};

function toEntry(e: CollectionEntry<'articles' | 'notebooks'>, kind: 'articles' | 'notebooks'): Entry {
  const c = e.data.collection;
  return {
    id: e.id,
    title: e.data.title,
    date: e.data.date,
    collection: typeof c === 'string' && c.length > 0 ? c : null,
    status: e.data.status ?? null,
    order: typeof e.data.order === 'number' ? e.data.order : null,
    kind,
  };
}

// Reading order within a collection: entries with an explicit `order` come
// first (ascending), then everything else newest-first (reverse-id). This lets
// the docs lay out a guided path while undated example lists stay chronological.
function byReadingOrder(a: Entry, b: Entry): number {
  if (a.order !== null && b.order !== null) return a.order - b.order;
  if (a.order !== null) return -1;
  if (b.order !== null) return 1;
  return b.id.localeCompare(a.id);
}

export async function loadAllEntries(): Promise<{ articles: Entry[]; notebooks: Entry[] }> {
  const [articles, notebooks] = await Promise.all([
    getCollection('articles'),
    getCollection('notebooks'),
  ]);
  return {
    articles: articles.map((e) => toEntry(e, 'articles')).sort(byReadingOrder),
    notebooks: notebooks.map((e) => toEntry(e, 'notebooks')).sort(byReadingOrder),
  };
}

export type Bucket = {
  collection: string;
  label: string;
  articles: Entry[];
  notebooks: Entry[];
};

export function bucketize(articles: Entry[], notebooks: Entry[]): Bucket[] {
  const map = new Map<string, Bucket>();
  const get = (name: string): Bucket => {
    if (!map.has(name)) {
      map.set(name, {
        collection: name,
        label: collectionLabel(name),
        articles: [],
        notebooks: [],
      });
    }
    return map.get(name)!;
  };
  for (const a of articles) get(a.collection ?? UNCOLLECTED).articles.push(a);
  for (const n of notebooks) get(n.collection ?? UNCOLLECTED).notebooks.push(n);
  const PINNED = ['in-progress', 'neuron-models', 'mujoco', 'streamlit'];
  const rank = (c: string) => {
    const i = PINNED.indexOf(c);
    return i === -1 ? Infinity : i;
  };
  return [...map.values()].sort((a, b) => {
    const ra = rank(a.collection);
    const rb = rank(b.collection);
    if (ra !== rb) return ra - rb;
    if (a.collection === UNCOLLECTED) return 1;
    if (b.collection === UNCOLLECTED) return -1;
    const totA = a.articles.length + a.notebooks.length;
    const totB = b.articles.length + b.notebooks.length;
    return totB - totA || a.collection.localeCompare(b.collection);
  });
}

export function formatDate(d: Date): string {
  const day = d.getUTCDate();
  const suffix =
    day % 100 >= 11 && day % 100 <= 13
      ? 'th'
      : day % 10 === 1 ? 'st'
      : day % 10 === 2 ? 'nd'
      : day % 10 === 3 ? 'rd'
      : 'th';
  const month = d.toLocaleDateString('en-GB', { month: 'short', timeZone: 'UTC' });
  return `${day}${suffix} ${month} ${d.getUTCFullYear()}`;
}
