// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import sharedConfig from '@geti/config/lint';

export default [
    ...sharedConfig,
    {
        rules: {
            'no-restricted-imports': [
                'error',
                {
                    patterns: [
                        {
                            group: ['./index.ts'],
                            message: 'Do not import from barrel file, use relative imports instead.',
                        },
                        {
                            group: ['../*/**'],
                            message: 'Do not import anything from outside ui package.',
                        },
                    ],
                },
            ],
        },
    },
];
