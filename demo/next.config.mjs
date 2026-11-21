import path from 'node:path';

export default {
  output: 'export',
  images: { unoptimized: true },
  turbopack: { root: path.resolve(import.meta.dirname, '..') },
  experimental: { cpus: 1, externalDir: true },
};
