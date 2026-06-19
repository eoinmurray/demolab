import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';
import { NOTEBOOK_STATUSES } from './config/status';

const entrySchema = z.object({
  title: z.string(),
  date: z.coerce.date(),
  description: z.string().optional(),
  collection: z.string().optional(),
  status: z.enum(NOTEBOOK_STATUSES).optional(),
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
