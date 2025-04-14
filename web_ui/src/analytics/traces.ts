// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { W3CTraceContextPropagator } from '@opentelemetry/core';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';
import { OTLPExporterNodeConfigBase } from '@opentelemetry/otlp-exporter-base';
import { Resource } from '@opentelemetry/resources';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import {
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    StackContextManager,
    WebTracerProvider,
} from '@opentelemetry/sdk-trace-web';
import { SemanticResourceAttributes } from '@opentelemetry/semantic-conventions';

import { API_URLS } from '../core/services/urls';
import { DEFAULT_EXPORTER_CONFIG, ResourceInfo } from './utils';

export const initializeTracing = (
    { serviceName, serviceVersion, workflowId }: ResourceInfo,
    router: typeof API_URLS
) => {
    const resource = Resource.default().merge(
        new Resource({
            [SemanticResourceAttributes.SERVICE_NAME]: serviceName,
            [SemanticResourceAttributes.SERVICE_VERSION]: serviceVersion,
            workflow_id: workflowId,
        })
    );

    // initialize provider
    const providerWithZone = new WebTracerProvider({ resource });

    const collectorOptions: OTLPExporterNodeConfigBase = {
        url: router.ANALYTICS.TRACES_EXPORTER,
        ...DEFAULT_EXPORTER_CONFIG,
    };

    if (process.env.NODE_ENV === 'development') {
        if (process.env.REACT_APP_ANALYTICS_CONSOLE_EXPORT === 'true') {
            const consoleExporter = new SimpleSpanProcessor(new ConsoleSpanExporter());
            providerWithZone.addSpanProcessor(consoleExporter);
        }
    }

    // batches traces and sends them in the bulks
    const oltpExporter = new BatchSpanProcessor(new OTLPTraceExporter(collectorOptions));
    providerWithZone.addSpanProcessor(oltpExporter);

    registerInstrumentations({
        instrumentations: [
            new XMLHttpRequestInstrumentation({
                clearTimingResources: true,
                ignoreUrls: [
                    new RegExp('api/v1/status'),
                    new RegExp('api/v1/workspaces/.*/jobs'),
                    new RegExp('api/v1/workspaces/.*/projects/.*/status'),
                ],
            }),
        ],
    });

    providerWithZone.register({
        contextManager: new StackContextManager(),
        propagator: new W3CTraceContextPropagator(),
    });

    return { providerWithZone };
};
