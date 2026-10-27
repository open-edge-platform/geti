// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { fixupConfigRules, fixupPluginRules } from '@eslint/compat';
import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';
import typescriptEslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import header from 'eslint-plugin-header';
import _import from 'eslint-plugin-import';
import jsxA11Y from 'eslint-plugin-jsx-a11y';
import reactPlugin from 'eslint-plugin-react';
import reactHooks from 'eslint-plugin-react-hooks';
import globals from 'globals';

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);
const compat = new FlatCompat({
    baseDirectory: dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all,
});

// https://github.com/sindresorhus/globals/issues/239
const GLOBALS_BROWSER_FIX = Object.assign({}, globals.browser, {
    AudioWorkletGlobalScope: 'readonly',
});

delete GLOBALS_BROWSER_FIX['AudioWorkletGlobalScope '];

// https://github.com/Stuk/eslint-plugin-header/issues/57#issuecomment-2378485611
header.rules.header.meta.schema = false;

export default [
    {
        ignores: [
            '**/build',
            '**/coverage',
            '**/node_modules',
            '**/*.tsx.snap',
            'src/assets',
            '**/public',
        ],
    },
    js.configs.recommended,
    ...fixupConfigRules(
        compat.extends(
            'plugin:jsx-a11y/recommended',
            'plugin:@typescript-eslint/recommended',
            'plugin:import/recommended',
            'plugin:import/typescript'
        )
    ),
    {
        files: ['src/**/*.tsx', 'src/**/*.ts'],
        ...reactPlugin.configs.flat.recommended,
    },
    ...reactHooks.configs.recommended.map((config) => ({
        ...config,
        files: ['src/**/*.tsx', 'src/**/*.ts'],
    })),
    {
        files: ['src/**/*.tsx', 'src/**/*.ts'],
        rules: {
            'react/jsx-props-no-spreading': ['off'],
            'react/no-unknown-property': [
                'error',
                {
                    ignore: ['transform-origin', 'onLoad'],
                },
            ],

            'react/require-default-props': 'off',
            'react/prop-types': 'off',
            'react/display-name': 'off',
            'react/react-in-jsx-scope': 'off',
            'react/jsx-filename-extension': [
                2,
                {
                    extensions: ['.js', '.jsx', '.ts', '.tsx'],
                },
            ],
            'react/default-props-match-prop-types': 'warn',
            'react/no-unused-prop-types': 'warn',
            'jsx-a11y/click-events-have-key-events': 'off',
            'jsx-a11y/no-noninteractive-element-interactions': 'off',
            'jsx-a11y/no-static-element-interactions': 'off',
        },
    },
    {
        plugins: {
            import: fixupPluginRules(_import),
            'jsx-a11y': fixupPluginRules(jsxA11Y),
            '@typescript-eslint': fixupPluginRules(typescriptEslint),
            header,
        },
        languageOptions: {
            globals: {
                ...GLOBALS_BROWSER_FIX,
            },
            parser: tsParser,
            ecmaVersion: 'latest',
            sourceType: 'module',

            parserOptions: {
                ecmaFeatures: {
                    jsx: true,
                },
            },
        },

        settings: {
            'import/resolver': {
                node: {
                    paths: ['src'],
                    extensions: ['.js', '.jsx', '.ts', '.tsx'],
                },

                typescript: {
                    alwaysTryTypes: true,
                    project: './tsconfig.json',
                },
            },

            react: {
                version: 'detect',
            },
        },

        rules: {
            '@typescript-eslint/no-unused-expressions': [
                'error',
                {
                    allowTernary: true,
                    allowShortCircuit: true,
                },
            ],
            '@typescript-eslint/no-duplicate-enum-values': ['off'],

            'no-underscore-dangle': ['error'],

            '@typescript-eslint/no-unused-vars': [
                'error',
                {
                    args: 'all',
                    argsIgnorePattern: '^_',
                    caughtErrors: 'all',
                    caughtErrorsIgnorePattern: '^_',
                    destructuredArrayIgnorePattern: '^_',
                    varsIgnorePattern: '^_',
                    ignoreRestSiblings: true,
                },
            ],

            'import/extensions': [
                'error',
                'ignorePackages',
                {
                    js: 'always',
                    jsx: 'never',
                    ts: 'never',
                    tsx: 'never',
                },
            ],

            'import/order': ['off'],

            'import/no-unresolved': [
                2,
                {
                    ignore: ['csstype'],
                },
            ],

            '@typescript-eslint/no-shadow': [
                'warn',
                {
                    builtinGlobals: false,
                    hoist: 'never',
                },
            ],

            '@typescript-eslint/ban-ts-comment': 'warn',
            '@typescript-eslint/no-non-null-assertion': 'error',
            'no-console': ['error', { allow: ['warn', 'error', 'time', 'timeEnd', 'info'] }],
            'object-shorthand': ['error', 'always'],
        },
    },
    {
        // Type-aware rules. Scoped to files covered by tsconfig.json `include`.
        files: ['{src,tests,mocks}/**/*.{ts,tsx}'],
        languageOptions: {
            parserOptions: {
                projectService: true,
                tsconfigRootDir: dirname,
            },
        },
        rules: {
            '@typescript-eslint/no-floating-promises': [
                'error',
                {
                    // In data-router mode `navigate()` returns a Promise that only signals navigation
                    // completion; errors go to the route's errorElement, so it is safe to not await it.
                    allowForKnownSafeCalls: [{ from: 'package', name: 'NavigateFunction', package: 'react-router' }],
                },
            ],
            '@typescript-eslint/no-misused-promises': ['error', { checksVoidReturn: { attributes: false } }],
            '@typescript-eslint/only-throw-error': 'error',
            '@typescript-eslint/await-thenable': 'error',
            '@typescript-eslint/switch-exhaustiveness-check': 'error',
        },
    },
];
