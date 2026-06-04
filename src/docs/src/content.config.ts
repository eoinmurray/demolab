import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const entrySchema = z.object({
  title: z.string(),
  date: z.coerce.date(),
  description: z.string().optional(),
  collection: z.string().optional(),
});

const notebooks = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/notebooks' }),
  schema: entrySchema,
});

const articles = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/articles' }),
  schema: entrySchema,
});

export const collections = { notebooks, articles };
