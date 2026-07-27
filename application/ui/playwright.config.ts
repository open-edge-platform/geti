// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { defineConfig, devices } from '@playwright/test';
import dotenv from 'dotenv';

const file = fileURLToPath(import.meta.url);
const dirname = path.dirname(file);

dotenv.config({
    path: path.resolve(dirname, '.env.test'),
});

const CI = !!process.env.CI;

const ACTION_TIMEOUT = 30000;

// In CI we serve pre-built bundles via `rsbuild preview`, which requires the
// output directories to already exist. Failing fast here produces a clearer
// error than waiting for `webServer.timeout` to elapse on a 404-returning
// preview server.
if (CI) {
    const requiredDirs = ['dist', 'dist-tauri'];
    for (const dir of requiredDirs) {
        const absolute = path.resolve(dirname, dir);
        if (!existsSync(absolute)) {
            throw new Error(
                `Missing build output at ${absolute}. ` +
                    `Run \`npm run build\` (web) and \`npm run build:tauri\` (tauri) before \`npm run test:component\`.`
            );
        }
    }
}

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
    /* Run tests in files in parallel */
    fullyParallel: true,
    /* Fail the build on CI if you accidentally left test.only in the source code. */
    forbidOnly: CI,
    /* Retry on CI only */
    retries: process.env.CI ? 2 : 0,
    /* Opt out of parallel tests on CI. */
    workers: process.env.CI ? 1 : undefined,
    /* Test timeout */
    timeout: CI ? 120000 : 60000,
    /* Expect timeout */
    expect: {
        timeout: CI ? 10000 : 5000,
    },
    /* Reporter to use. See https://playwright.dev/docs/test-reporters */
    reporter: [[CI ? 'github' : 'list'], ['html', { open: 'never' }]],
    use: {
        baseURL: 'http://localhost:3000',
        trace: CI ? 'on-first-retry' : 'on',
        video: CI ? 'on-first-retry' : 'on',
        launchOptions: {
            slowMo: 100,
            headless: true,
            args: ['--auto-open-devtools-for-tabs'],
        },
        timezoneId: 'UTC',
        actionTimeout: ACTION_TIMEOUT,
        navigationTimeout: ACTION_TIMEOUT,
    },

    /* Configure projects for major browsers */
    projects: [
        {
            name: 'component',
            testDir: './tests',
            testIgnore: ['**/e2e/**', /.*\.tauri\.spec\.ts/],
            use: {
                ...devices['Desktop Chrome'],
                headless: true,
                viewport: { width: 1280, height: 720 },
            },
        },
        {
            name: 'Tauri component tests',
            testDir: './tests',
            use: {
                ...devices['Desktop Chrome'],
                headless: true,
                viewport: { width: 1280, height: 720 },
                baseURL: 'http://localhost:3001',
            },
            testMatch: /.*\.tauri\.spec\.ts$/,
        },
        {
            name: 'e2e',
            testDir: './tests/e2e',
            use: {
                ...devices['Desktop Chrome'],
                headless: CI,
                viewport: { width: 1280, height: 720 },
            },
        },
    ],

    /* Run your local dev server(s) before starting the tests */
    webServer: !process.env.ENABLE_BACKEND
        ? [
              {
                  command: CI ? 'npm run preview -- --port 3000' : 'npm run start',
                  url: 'http://localhost:3000',
                  reuseExistingServer: true,
                  timeout: ACTION_TIMEOUT,
              },
              {
                  command: CI ? 'npm run preview:tauri' : 'npm run start:tauri -- --port 3001',
                  url: 'http://localhost:3001',
                  reuseExistingServer: true,
                  timeout: ACTION_TIMEOUT,
              },
          ]
        : undefined,
});
