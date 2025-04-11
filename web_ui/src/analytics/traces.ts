// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
