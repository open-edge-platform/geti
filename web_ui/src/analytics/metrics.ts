// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { API_URLS } from '@geti/core';
import { metrics } from '@opentelemetry/api';
import { OTLPMetricExporter } from '@opentelemetry/exporter-metrics-otlp-http';
import { Resource } from '@opentelemetry/resources';
import { ConsoleMetricExporter, MeterProvider, PeriodicExportingMetricReader } from '@opentelemetry/sdk-metrics';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

import { DEFAULT_EXPORTER_CONFIG, ResourceInfo } from './utils';

export const getMetricName = (suffix: string) => `geti.application.ui.${suffix}`;

const EXPORT_INTERVAL_IN_MILLIS = 20 * 1000; // 20 seconds

export const createPeriodicMetricExporter = (router: typeof API_URLS) => {
    return new PeriodicExportingMetricReader({
        exporter: new OTLPMetricExporter({
            url: router.ANALYTICS.METRICS_EXPORTER,
            ...DEFAULT_EXPORTER_CONFIG,
        }),
        exportIntervalMillis: EXPORT_INTERVAL_IN_MILLIS,
    });
};

export const initializeMetrics = (
    { serviceName, serviceVersion }: Omit<ResourceInfo, 'workflowId'>,
    router: typeof API_URLS
) => {
    const resource = Resource.default().merge(
        new Resource({
            [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
            [SemanticResourceAttributes.SERVICE_VERSION]: serviceVersion,
        })
    );

    const meterProvider = new MeterProvider({ resource });
    let exporter: PeriodicExportingMetricReader | null = null;

    if (process.env.NODE_ENV !== 'test') {
        exporter = createPeriodicMetricExporter(router);

        if (process.env.REACT_APP_ANALYTICS_CONSOLE_EXPORT === 'true') {
            const consoleExporter = new PeriodicExportingMetricReader({
                exporter: new ConsoleMetricExporter(),
                exportIntervalMillis: EXPORT_INTERVAL_IN_MILLIS,
            });

            meterProvider.addMetricReader(consoleExporter);
        }

        meterProvider.addMetricReader(exporter);
    }

    metrics.setGlobalMeterProvider(meterProvider);

    return {
        meterProvider,
        exporter,
    };
};
