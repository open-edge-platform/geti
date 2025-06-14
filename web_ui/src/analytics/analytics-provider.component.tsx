// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, ReactNode, useContext, useEffect, useMemo, useRef, useState } from 'react';

import { useApplicationServices } from '@geti/core/src/services/application-services-provider.component';
import { Meter } from '@opentelemetry/api';
import { MeterProvider, PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';

import { useFeatureFlags } from '../core/feature-flags/hooks/use-feature-flags.hook';
import { useWorkflowId } from '../core/platform-utils/hooks/use-platform-utils.hook';
import { useEventListener } from '../hooks/event-listener/event-listener.hook';
import { createPeriodicMetricExporter, initializeMetrics } from './metrics';
import { initializeTracing } from './traces';
import { SERVICE_DEFAULT_INFO } from './utils';

interface AnalyticsContextProps {
    getTrace: ((name: string) => void) | undefined;
    meter: Meter | undefined;
}

interface AnalyticsProviderProps {
    children: ReactNode;
}

const AnalyticsContext = createContext<AnalyticsContextProps | undefined>(undefined);

const AnalyticsProvider = ({ children }: AnalyticsProviderProps): JSX.Element => {
    const [isWindowFocus, setIsWindowFocus] = useState<boolean>(true);
    const [isDocumentContentVisible, setIsDocumentContentVisible] = useState<boolean>(true);
    const { data: workflowId } = useWorkflowId();

    const tracingRef = useRef<{ getTrace: (name: string) => void } | null>(null);

    const exporterRef = useRef<PeriodicExportingMetricReader | null>(null);
    const meterProviderRef = useRef<MeterProvider | null>(null);

    /* NOTE: below listeners and check conditions are needed to fix idle session expiration issue */
    useEventListener('visibilitychange', () => {
        setIsDocumentContentVisible(!document.hidden && document.visibilityState === 'visible');
    });

    useEventListener('focus', () => {
        setIsWindowFocus(true);
    });

    useEventListener('blur', () => {
        setIsWindowFocus(false);
    });

    const { router } = useApplicationServices();

    useEffect(() => {
        if (workflowId === undefined) {
            return;
        }

        if (meterProviderRef.current === null && exporterRef.current === null) {
            const { exporter, meterProvider } = initializeMetrics(SERVICE_DEFAULT_INFO, router);

            exporterRef.current = exporter;
            meterProviderRef.current = meterProvider;
        } else if ((!isWindowFocus || !isDocumentContentVisible) && exporterRef.current !== null) {
            // shutdown metric exporter when either window is not focused or document content is not visible
            exporterRef.current?.shutdown().then(() => {
                exporterRef.current = null;
            });
        } else if (isWindowFocus && isDocumentContentVisible && exporterRef.current === null) {
            // switch on the metric exporter when window is focused and document content is visible
            const exporter = createPeriodicMetricExporter(router);

            meterProviderRef.current?.addMetricReader(exporter);
            exporterRef.current = exporter;
        }

        if (tracingRef.current === null) {
            const trace = initializeTracing({ ...SERVICE_DEFAULT_INFO, workflowId }, router);

            tracingRef.current = {
                getTrace: (name: string) => trace.providerWithZone.getTracer(name),
            };
        }
    }, [workflowId, isWindowFocus, isDocumentContentVisible, router]);

    const value = useMemo<AnalyticsContextProps>(
        () => ({
            meter: meterProviderRef.current?.getMeter('default', SERVICE_DEFAULT_INFO.serviceVersion),
            getTrace: tracingRef.current?.getTrace,
        }),
        []
    );

    return <AnalyticsContext.Provider value={value}>{children}</AnalyticsContext.Provider>;
};

const useAnalytics = (): AnalyticsContextProps => {
    const context = useContext(AnalyticsContext);

    if (context === undefined) {
        return {
            meter: undefined,
            getTrace: undefined,
        };
    }

    return context;
};

const useIsAnalyticsEnabled = (): boolean => {
    const { FEATURE_FLAG_TELEMETRY_STACK } = useFeatureFlags();

    return FEATURE_FLAG_TELEMETRY_STACK;
};

export { AnalyticsProvider, useAnalytics, useIsAnalyticsEnabled };
