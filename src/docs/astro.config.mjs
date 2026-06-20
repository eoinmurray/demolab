import { defineConfig } from 'astro/config';
import mdx from '@astrojs/mdx';
import tailwindcss from '@tailwindcss/vite';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

export default defineConfig({
  // Serve config is env-driven so the site can be embedded as a docs subfolder
  // of another project without editing source. Defaults preserve standalone use.
  site: process.env.PUBLIC_SITE_URL ?? 'https://eoinmurray.github.io',
  base: process.env.PUBLIC_BASE_PATH ?? '/demolab',
  devToolbar: { enabled: false },
  integrations: [mdx()],
  markdown: {
    remarkPlugins: [remarkMath],
    rehypePlugins: [rehypeKatex],
    shikiConfig: { theme: 'github-light' },
  },
  vite: {
    plugins: [tailwindcss()],
  },
});
