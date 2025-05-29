// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, ReactNode } from 'react';

import { AnalyticsProvider } from '../analytics/analytics-provider.component';
import { useProductInfo } from '../core/platform-utils/hooks/use-platform-utils.hook';

interface InstallationModeProviderProps {
    children: ReactNode;
}

export const InstallationModeProvider: FC<InstallationModeProviderProps> = ({ children }) => {
    const { data } = useProductInfo();

    if (data.installationMode === 'standard') {
        return <AnalyticsProvider>{children}</AnalyticsProvider>;
    }

    return <>{children}</>;
};
