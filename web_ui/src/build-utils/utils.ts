// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createRoot } from 'react-dom/client';

const container = document.getElementById('root') as HTMLElement;
const root = createRoot(container);

export { root };

export { default as reportWebVitals } from '../report-web-vitals';

export { register as serviceWorkerRegistration } from '../serviceWorkerRegistration';
