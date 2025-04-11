// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { defineConfig, devices, PlaywrightTestConfig } from '@playwright/test';

const CI = !!process.env.CI;
const CI_E2E = !!process.env.PW_E2E;

const viewport = { height: 1080, width: 1920 };
const viewportMini = { height: 1024, width: 768 };

const permissions = ['clipboard-write'];

const config: PlaywrightTestConfig = defineConfig({
    testDir: 'tests/features',
    forbidOnly: !!process.env.CI,
    retries: process.env.CI ? 2 : 0,
    workers: 1,
    use: {
        baseURL: 'http://localhost:3000',
        viewport,
        trace: CI ? 'on-first-retry' : 'on',
        video: CI ? 'on-first-retry' : 'on',
        launchOptions: {
            slowMo: 100,
            headless: true, // use the --headed option to turn on headed mode
            devtools: false,
            args: ['--use-fake-ui-for-media-stream', '--use-fake-device-for-media-stream'],
        },
        timezoneId: 'UTC',
        actionTimeout: CI ? 10000 : 5000,
        navigationTimeout: CI ? 10000 : 5000,
        permissions,
    },
    expect: {
        timeout: 1000 * 60,
    },
    // We set the timeout to 5 minutes per test, though ideally we should be stricter,
    // we will reevaluate this value later on
    timeout: 5 * 60 * 1000,
    webServer: CI_E2E
        ? undefined
        : {
              command: CI ? 'serve -s build -p 3000 -c ../serve.json' : 'npm run start',
              port: 3000,
              timeout: 5 * 60 * 1000,
              reuseExistingServer: true,
          },
    // default 'list' when running locally
    reporter: [
        [CI ? 'github' : 'list'],
        [CI ? 'blob' : 'html', { open: 'never' }],
        ['json', { outputFile: 'playwright-report.' + process.env.HOSTNAME + '.json' }],
    ],
    projects: [
        {
            name: 'chromium',
            grepInvert: /mobile/,
            use: {
                ...devices['Desktop Chrome'],
                viewport,
            },
        },
        {
            name: 'chromium mini viewport',
            grep: /mobile/,
            use: {
                ...devices['Desktop Chrome'],
                viewport: viewportMini,
                isMobile: true,
            },
        },
        {
            name: 'e2e-setup',
            testDir: 'tests/e2e/setup',
            testMatch: /.*\.setup\.ts/,
            timeout: 1000 * 60 * 20,
            expect: {
                timeout: 1000 * 60,
            },
            retries: CI ? 1 : 0,
            use: {
                ...devices['Desktop Chrome'],
                trace: CI ? 'retain-on-failure' : 'on',
                video: CI ? 'retain-on-failure' : 'on',
                viewport,
                actionTimeout: CI ? 60_000 : 5000,
                navigationTimeout: CI ? 60_000 : 5000,
            },
        },
        {
            name: 'e2e',
            testDir: 'tests/e2e',
            // The e2e tests are expected to take long as some of them may need to
            // wait for training to be finished
            timeout: 1000 * 60 * 20,
            expect: {
                timeout: 1000 * 60,
            },
            dependencies: ['e2e-setup'],
            retries: 0,
            use: {
                ...devices['Desktop Chrome'],
                trace: CI ? 'retain-on-failure' : 'on',
                video: CI ? 'retain-on-failure' : 'on',
                viewport,
                actionTimeout: CI ? 60_000 : 5000,
                navigationTimeout: CI ? 60_000 : 5000,
            },
        },
    ],
});

process.env.PLAYWRIGHT_EXPERIMENTAL_FEATURES = '1';
process.env.PLAYWRIGHT_ENV = 'true';

export default config;
