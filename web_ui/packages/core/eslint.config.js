// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import sharedConfig from '@geti/config/lint';

export default [
    ...sharedConfig,
    {
        files: ['./index.ts'],
        rules: {
            'no-restricted-imports': [
                'error',
                {
                    patterns: [
                        {
                            group: ['@geti/core'],
                            message: 'Importing files from @geti/ui is not allowed.',
                        },
                        {
                            group: ['../**/*'],
                            message: 'Importing files outside of the current package is not allowed.',
                        },
                    ],
                },
            ],
        },
    },
    {
        files: ['./src/**/*.{ts,tsx}'],
        rules: {
            'no-restricted-imports': [
                'error',
                {
                    patterns: [
                        {
                            group: ['@geti/core'],
                            message: 'Importing files from @geti/core is not allowed.',
                        },
                    ],
                },
            ],
        },
    },
];
