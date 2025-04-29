// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { reportWebVitals, root, serviceWorkerRegistration } from './build-utils/utils';
import { InfrastructureProviders } from './providers/infrastructure-providers.component';
import { appRoutes } from './routes/app-routes.component';

root.render(<InfrastructureProviders routes={[appRoutes]} />);

reportWebVitals();

serviceWorkerRegistration();
