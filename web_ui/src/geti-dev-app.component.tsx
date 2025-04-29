// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { App } from './app.component';
import { reportWebVitals, root, serviceWorkerRegistration } from './build-utils/utils';

root.render(<App />);

reportWebVitals();

serviceWorkerRegistration();
