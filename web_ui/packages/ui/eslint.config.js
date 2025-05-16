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
                            group: ['../../**/*'],
                            message: 'Importing files outside of the current package is not allowed.',
                        },
                    ],
                },
            ],
        },
    },
];
