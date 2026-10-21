import js from '@eslint/js';
import tseslint from 'typescript-eslint';

export default tseslint.config(
  {
    ignores: [
      '**/dist/**',
      '**/.next/**',
      '**/node_modules/**',
      '.local/**',
      'apps/api/src/generated/**',
    ],
  },
  js.configs.recommended,
  ...tseslint.configs.recommended,
  {
    files: ['**/*.mjs', 'apps/api/**/*.ts'],
    languageOptions: {
      globals: {
        process: 'readonly',
        console: 'readonly',
        URL: 'readonly',
        Buffer: 'readonly',
        setTimeout: 'readonly',
        setInterval: 'readonly',
        clearInterval: 'readonly',
        structuredClone: 'readonly',
        fetch: 'readonly',
        AbortSignal: 'readonly',
      },
    },
  },
  {
    files: ['tests/e2e/*.mjs'],
    languageOptions: {
      globals: {
        document: 'readonly',
        window: 'readonly',
        localStorage: 'readonly',
        Event: 'readonly',
      },
    },
  },
);
