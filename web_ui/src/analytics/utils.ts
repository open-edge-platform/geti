// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
