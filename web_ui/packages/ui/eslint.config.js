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
                            group: ['@geti/ui'],
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
        files: ['./src/**/*.{js,jsx,ts,tsx,css,scss}'],
        rules: {
            'no-restricted-imports': [
                'error',
                {
                    patterns: [
                        {
                            group: ['../../**/*', '!../**/icons'],
                            message: 'Importing files outside of the current package is not allowed except /icons.',
                        },
                        {
                            group: ['@geti/ui'],
                            message: 'Importing files from @geti/ui is not allowed.',
                        },
                    ],
                },
            ],
        },
    },
];
