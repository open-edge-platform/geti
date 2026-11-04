// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MqttSinkConfig } from '@/api/types';
import type { TranslateFn } from '@/i18n';

export const getMqttInitialConfig = (t: TranslateFn): MqttSinkConfig => ({
    id: '',
    name: t('inference.sinks.defaultNames.mqtt'),
    topic: '',
    sink_type: 'mqtt',
    rate_limit: null,
    broker_host: '',
    broker_port: 0,
    auth_required: false,
    output_formats: [],
});

export const isMqttConfigComplete = ({ broker_host, output_formats }: MqttSinkConfig): boolean =>
    broker_host.trim().length > 0 && output_formats.length > 0;
