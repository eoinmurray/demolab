import { defineConfig } from 'astro/config';
import { loadEnv } from 'vite';
import mdx from '@astrojs/mdx';
import tailwindcss from '@tailwindcss/vite';
import remarkMath from 'remark-math';
import rehypeKatex from 'rehype-katex';

// Load .env files (incl. mode-specific .env.development / .env.production) so
// serve config can be overridden per-mode without editing source. Real shell
// env vars still win.
const mode = process.env.NODE_ENV ?? 'production';
const env = { ...loadEnv(mode, process.cwd(), 'PUBLIC_'), ...process.env };

export default defineConfig({
  // Serve config is env-driven so the site can be embedded as a docs subfolder
  // of another project without editing source. Defaults preserve standalone use.
  // Standalone, the site is published at the custom domain demolab.eoinmurray.info,
  // served at the root — so base is '/'. To host it under a path (e.g. a
  // project subfolder, or username.github.io/demolab) set PUBLIC_BASE_PATH.
  site: env.PUBLIC_SITE_URL ?? 'https://demolab.eoinmurray.info',
  base: env.PUBLIC_BASE_PATH ?? '/',
  server: { port: 3000 },
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
