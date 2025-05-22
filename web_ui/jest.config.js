// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import sharedConfig from '@geti/config/test';

export default {
    ...sharedConfig,
    roots: ['<rootDir>/src', '<rootDir>/packages/'],
    projects: ['<rootDir>', '<rootDir>/packages/*'],
    collectCoverageFrom: ['src/**/*.{js,jsx,ts,tsx}', '!src/**/*.d.ts'],
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
};
