// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import React from 'react';

import ReactDOM from 'react-dom/client';

import '@/i18n';

import { FEATURE_FLAGS } from './constants/feature-flags';
import { setupStorageCleanup } from './platform/storage-cleanup';
import { Providers } from './providers';

import './index.css';
import './shared/styles/view-transitions.scss';

setupStorageCleanup();

// TODO(#7810): delete once the OME backend is merged, with shared/ome-demo*.ts, public/mockServiceWorker.js and
// `msw.workerDirectory` in package.json.
// Without service workers (e.g. Tauri) the app runs without the demo images
const startOmeDemo = async () => {
    if (FEATURE_FLAGS.OME_DEMO) {
        await import('./shared/ome-demo-worker').then(({ startOmeDemoWorker }) => startOmeDemoWorker()).catch(() => {});
    }
};

const rootEl = document.getElementById('root');
if (rootEl) {
    void startOmeDemo().then(() => {
        ReactDOM.createRoot(rootEl).render(
            <React.StrictMode>
                <Providers />
            </React.StrictMode>
        );
    });
}
