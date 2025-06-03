// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { AnalyticsProvider, useIsAnalyticsEnabled } from '../analytics/analytics-provider.component';

interface InstallationModeProviderProps {
    children: ReactNode;
}

export const InstallationModeProvider: FC<InstallationModeProviderProps> = ({ children }) => {
    const isAnalyticsEnabled = useIsAnalyticsEnabled();

    if (isAnalyticsEnabled) {
        return <AnalyticsProvider>{children}</AnalyticsProvider>;
    }

    return <>{children}</>;
};
