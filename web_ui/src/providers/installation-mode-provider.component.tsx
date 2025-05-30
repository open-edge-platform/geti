// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { AnalyticsProvider } from '../analytics/analytics-provider.component';

interface InstallationModeProviderProps {
    children: ReactNode;
}

type InstallationMode = 'standard' | 'lite';

const installationMode: InstallationMode = 'lite';

export const InstallationModeProvider: FC<InstallationModeProviderProps> = ({ children }) => {

    if (installationMode === 'standard') {
        return <AnalyticsProvider>{children}</AnalyticsProvider>;
    }

    return <>{children}</>;
};
