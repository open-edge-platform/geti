// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import sharedConfig from '@geti/config/test';

export default {
    projects: [
        {
            ...sharedConfig,
            displayName: '@geti/main',
            roots: ['<rootDir>/src'],
            testMatch: ['<rootDir>/src/**/*.{test,spec}.{js,jsx,ts,tsx}'],
            setupFilesAfterEnv: ['<rootDir>/src/setupTests.tsx'],
            coveragePathIgnorePatterns: [
                'src/service-worker.ts',
                'src/serviceWorkerRegistration.ts',
                'src/webworkers',
                'src/hooks/use-worker/utils.ts',
                'src/report-web-vitals.ts',
                'src/app.component.tsx',
                'src/index.tsx',
                'src/assets',
                'src/e2e',
                'src/intel-admin-app',
                'src/sign-up',
                'dev-proxy.ts',
                'tests',
            ],
        },
        '<rootDir>/packages/*/jest.config.js',
    ],
    collectCoverageFrom: [
        '<rootDir>/src/**/*{test,spec}.{js,jsx,ts,tsx}',
        '<rootDir>/packages/**/*{test,spec}.{js,jsx,ts,tsx}',
    ],
    coverageReporters: ['clover', 'json', 'json-summary'],
    coverageThreshold: {
        global: {
            lines: 75,
        },
    },
};
