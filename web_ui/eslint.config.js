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
                    name: '@adobe/react-spectrum',
                    importNames: ['Button'],
                    message: "Use 'Button' from @geti/ui folder instead.",
                },
                {
                    name: '@adobe/react-spectrum',
                    importNames: ['SpectrumButtonProps'],
                    message: "Use 'SpectrumButtonProps' from @geti/ui folder instead.",
                },
                {
                    name: '@react-types/button',
                    importNames: ['SpectrumButtonProps'],
                    message: "Use 'SpectrumButtonProps' from @geti/ui folder instead.",
                },
                {
                    name: '@adobe/react-spectrum',
                    importNames: ['ActionButton'],
                    message: "Use 'ActionButton' from @geti/ui folder instead.",
                },
                {
                    name: '@adobe/react-spectrum',
                    importNames: ['SpectrumActionButtonProps'],
                    message: "Use 'SpectrumActionButtonProps' from @geti/ui folder instead.",
                },
                {
                    name: '@react-types/button',
                    importNames: ['SpectrumActionButtonProps'],
                    message: "Use 'SpectrumActionButtonProps' from @geti/ui folder instead.",
                },
                {
                    name: '@adobe/react-spectrum',
                    importNames: ['Checkbox'],
                    message: "Use 'Checkbox' from @geti/ui folder instead.",
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
