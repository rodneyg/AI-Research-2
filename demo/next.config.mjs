import path from 'node:path';

export default {
  basePath: process.env.NEXT_PUBLIC_BASE_PATH ?? '',
  output: 'export',
  images: { unoptimized: true },
  turbopack: { root: path.resolve(import.meta.dirname, '..') },
  experimental: { cpus: 1, externalDir: true },
};
