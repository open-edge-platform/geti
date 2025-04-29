// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { InfrastructureProviders } from './providers/infrastructure-providers.component';
import { appRoutes } from './routes/app-routes.component';
import { intelAdminRoutes } from './routes/intel-admin-routes';

export const App = () => {
    return <InfrastructureProviders routes={[appRoutes, intelAdminRoutes]} />;
};
