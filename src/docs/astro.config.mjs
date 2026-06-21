import { defineConfig } from 'astro/config';
import { loadEnv } from 'vite';
import mdx from '@astrojs/mdx';
import tailwindcss from '@tailwindcss/vite';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// Load .env files (incl. mode-specific .env.development / .env.production) so
// serve config can be overridden per-mode. `astro dev` runs in development
// mode, `astro build` in production. Real shell env vars still win.
const mode = process.env.NODE_ENV ?? 'production';
const env = { ...loadEnv(mode, process.cwd(), 'PUBLIC_'), ...process.env };

export default defineConfig({
  // Serve config is env-driven so the site can be embedded as a docs subfolder
  // of another project without editing source. Defaults preserve standalone use.
  // .env.development sets PUBLIC_BASE_PATH=/ so local dev serves at the root,
  // while the Pages build (production mode) has no override and keeps /demolab.
  site: env.PUBLIC_SITE_URL ?? 'https://eoinmurray.github.io',
  base: env.PUBLIC_BASE_PATH ?? '/demolab',
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
