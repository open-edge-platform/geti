// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { OTLPExporterNodeConfigBase } from '@opentelemetry/otlp-exporter-base';

import packageJson from '../../package.json';
import { CSRF_HEADERS } from '../core/services/security';

export interface ResourceInfo {
    serviceName: string;
    serviceVersion: string;
    workflowId: string;
}

const SERVICE_VERSION = packageJson.version;
const SERVICE_NAME = 'intel-geti';

export const SERVICE_DEFAULT_INFO: Omit<ResourceInfo, 'workflowId'> = {
    serviceName: SERVICE_NAME,
    serviceVersion: SERVICE_VERSION,
};

export const DEFAULT_EXPORTER_CONFIG: Partial<OTLPExporterNodeConfigBase> = {
    headers: {
        Accept: 'application/json',
        ...CSRF_HEADERS,
    },
};
