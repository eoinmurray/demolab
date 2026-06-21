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

const notebooks = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './content/notebooks' }),
  schema: entrySchema,
});

const articles = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './content/articles' }),
  schema: entrySchema,
});

export const collections = { notebooks, articles };
