import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { NOTEBOOK_STATUSES } from './config/status';

const entrySchema = z.object({
  title: z.string(),
  date: z.coerce.date(),
  description: z.string().optional(),
  collection: z.string().optional(),
  status: z.enum(NOTEBOOK_STATUSES).optional(),
  // Optional reading-order weight within a collection (lower = earlier). Use it
  // to lay out a guided path; entries without it fall back to reverse-id order.
  order: z.number().optional(),
});

// Entries all live in the top-level ../entries/ dir (siblings of demolab-web).
// Split by filename: nb* are notebooks, ar* are articles. Non-.md/.mdx entries
// (e.g. Typst .typ) are ignored here — they're built by their own publisher.
const notebooks = defineCollection({
  loader: glob({ pattern: 'nb*.{md,mdx}', base: '../entries' }),
  schema: entrySchema,
});

const articles = defineCollection({
  loader: glob({ pattern: 'ar*.{md,mdx}', base: '../entries' }),
  schema: entrySchema,
});

export const collections = { notebooks, articles };
