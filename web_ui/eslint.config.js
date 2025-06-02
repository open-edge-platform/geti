// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { FlatCompat } from '@eslint/eslintrc';
import js from '@eslint/js';
import sharedEslintConfig from '@geti/config/lint';

const filename = fileURLToPath(import.meta.url);
const dirname = path.dirname(filename);
const compat = new FlatCompat({
    baseDirectory: dirname,
    recommendedConfig: js.configs.recommended,
    allConfig: js.configs.all,
});

export default [
    ...sharedEslintConfig,
    {
        rules: {
            'no-restricted-imports': [
                'error',
                {
                    paths: [
                        {
                            name: '@adobe/react-spectrum',
                            message: 'Use component from the @geti/ui folder instead.',
                        },
                    ],
                    patterns: [
                        {
                            group: ['@react-spectrum/*'],
                            message: 'Use component from the @geti/ui folder instead.',
                        },
                        {
                            group: ['@react-types/*'],
                            message: 'Use type from the @geti/ui folder instead.',
                        },
                        {
                            group: ['@spectrum-icons'],
                            message: 'Use icons from the @geti/ui/icons folder instead.',
                        },
                        {
                            group: ['react-aria-components'],
                            message: 'Use components from the @geti/ui folder instead.',
                        },
                    ],
                },
            ],
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
