// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { fixupConfigRules, fixupPluginRules } from '@eslint/compat';
import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';
import typescriptEslint from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import header from 'eslint-plugin-header';
import _import from 'eslint-plugin-import';
import jest from 'eslint-plugin-jest';
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
    AudioWorkletGlobalScope: globals.browser['AudioWorkletGlobalScope '],
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
            'src/assets\\(!/icons/**/index.ts)',
            'src/opencv-types',
            'src/__mocks__',
            '**/dex_templates',
            '**/oauth2_proxy_templates',
            '**/public',
            'src/core/server/generated/*',
        ],
    },
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
    {
        files: ['src/**/*.tsx', 'src/**/*.ts'],
        plugins: {
            'react-hooks': fixupPluginRules(reactHooks),
        },
        rules: {
            ...reactHooks.configs.recommended.rules,
            'react/jsx-props-no-spreading': ['off'],
            'react/no-unknown-property': [
                'error',
                {
                    ignore: ['transform-origin', 'onLoad'],
                },
            ],

            'react/jsx-indent-props': ['error', 4],
            'react-hooks/rules-of-hooks': 'error',
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
            jest,
            'jsx-a11y': fixupPluginRules(jsxA11Y),
            '@typescript-eslint': fixupPluginRules(typescriptEslint),
            header,
        },
        languageOptions: {
            globals: {
                ...GLOBALS_BROWSER_FIX,
            },
            parser: tsParser,
            ecmaVersion: 11,
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
            'max-len': [
                'error',
                {
                    code: 120,
                    ignorePattern: '^import .*',
                },
            ],

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

            'jest/no-disabled-tests': 'error',
            'jest/no-focused-tests': 'error',
            'jest/no-identical-title': 'error',
            'jest/prefer-to-have-length': 'warn',
            'jest/valid-expect': 'error',

            'import/extensions': [
                'error',
                'ignorePackages',
                {
                    js: 'never',
                    jsx: 'never',
                    ts: 'never',
                    tsx: 'never',
                },
            ],

            'import/order': ['off'],

            'no-restricted-imports': [
                'error',
                {
                    name: '@adobe/react-spectrum',
                    importNames: ['Button'],
                    message: "Use 'Button' from shared folder instead.",
                },
                {
                    name: '@adobe/react-spectrum',
                    importNames: ['ActionButton'],
                    message: "Use 'ActionButton' from shared folder instead.",
                },
            ],

            'import/no-unresolved': [
                2,
                {
                    ignore: ['opencv-types', 'OpenCVTypes', '^@.*', 'csstype', 'opencv'],
                },
            ],

            'header/header': [
                'warn',
                'line',
                [
                    ' INTEL CONFIDENTIAL',
                    '',
                    {
                        pattern: ' Copyright \\(C\\) \\d{4} Intel Corporation',
                        template: ' Copyright (C) 2025 Intel Corporation',
                    },
                    '',
                    ' This software and the related documents are Intel copyrighted materials, and your use of them is governed by',
                    ' the express license under which they were provided to you ("License"). Unless the License provides otherwise,',
                    ' you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents',
                    " without Intel's prior written permission.",
                    '',
                    ' This software and the related documents are provided as is, with no express or implied warranties,',
                    ' other than those that are expressly stated in the License.',
                ],
            ],

            '@typescript-eslint/no-shadow': [
                'warn',
                {
                    builtinGlobals: false,
                    hoist: 'never',
                },
            ],

            '@typescript-eslint/ban-ts-comment': 'warn',
            'no-console': ['error', { allow: ['warn', 'error', 'time', 'timeEnd', 'info'] }],
            'object-shorthand': ['error', 'always'],
        },
    },
    {
        files: ['**/*.test.tsx', '**/*.test.ts'],

        rules: {
            'max-len': 'off',
            '@typescript-eslint/no-non-null-assertion': 'error',
        },
    },

    ...compat.extends('plugin:playwright/playwright-test').map((config) => ({
        ...config,
        files: ['tests/features/**/*.ts', 'tests/utils/**/*.ts', 'tests/fixtures/**/*.ts', 'tests/e2e/**/*.ts'],
    })),
    {
        files: ['tests/features/**/*.ts', 'tests/utils/**/*.ts', 'tests/fixtures/**/*.ts', 'tests/e2e/**/*.ts'],

        rules: {
            'playwright/no-wait-for-selector': ['off'],
            'playwright/no-conditional-expect': ['off'],
            'playwright/no-standalone-expect': ['off'],
            'playwright/missing-playwright-await': ['warn'],
            'playwright/valid-expect': ['warn'],
            'playwright/no-useless-not': ['warn'],
            'playwright/no-page-pause': ['warn'],
            'playwright/prefer-to-have-length': ['warn'],
            'playwright/no-conditional-in-test': ['off'],
            'playwright/expect-expect': ['off'],
            'playwright/no-skipped-test': ['off'],
            'playwright/no-wait-for-timeout': ['off'],
            'playwright/no-nested-step': ['off'],
        },
    },
];
