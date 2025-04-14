// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext } from 'react';

import { ValueType } from '@opentelemetry/api';

import { useAnalytics } from '../../analytics/analytics-provider.component';
import { getMetricName } from '../../analytics/metrics';
import { usePWA } from '../../hooks/use-pwa/use-pwa.hook';

interface UseCollectPWAInstallationMetric {
    collectPWAInstallation: () => void;
}

const useCollectPWAInstallationMetric = (): UseCollectPWAInstallationMetric => {
    const { meter } = useAnalytics();

    const collectPWAInstallation = () => {
        const pwaInstallationCounter = meter?.createCounter(getMetricName('progressive_web_app'), {
            description: 'Metrics for Progressive Web App installation',
            valueType: ValueType.INT,
        });

        pwaInstallationCounter?.add(1);
    };

    return { collectPWAInstallation };
};

type ContextType = ReturnType<typeof usePWA>;
const ProgressiveWebAppContext = createContext<ContextType | undefined>(undefined);
export const ProgressiveWebAppProvider = ({ children }: { children: ReactNode }) => {
    const value = usePWA();

    return <ProgressiveWebAppContext.Provider value={value}>{children}</ProgressiveWebAppContext.Provider>;
};

export const useProgressiveWebApp = (): ContextType => {
    const context = useContext(ProgressiveWebAppContext);
    const { collectPWAInstallation } = useCollectPWAInstallationMetric();

    if (context === undefined) {
        // This context is not critical so we won't throw an error here,
        // instead we defautl to a situation where installing a PWA is disabled
        return {
            isPWAReady: false,
            handlePromptInstallApp: async () => false,
        };
    }

    return {
        isPWAReady: context.isPWAReady,
        handlePromptInstallApp: async () => {
            const wasInstalled = await context.handlePromptInstallApp();

            if (wasInstalled) {
                collectPWAInstallation();
            }

            return wasInstalled;
        },
    };
};
