// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { MqttSinkConfig } from '@/api/types';

import { EditSink } from '../deprecated/edit-sink/edit-sink.component';
import { Mqtt } from '../deprecated/mqtt/mqtt.component';
import { mqttBodyFormatter } from '../deprecated/mqtt/utils';
import type { EditSinkProps } from '../types';

export const EditMqttSink = ({ sink, isConnected, onSaved, onBackToList }: EditSinkProps<MqttSinkConfig>) => (
    <EditSink
        config={sink}
        isConnected={isConnected}
        onSaved={onSaved}
        onBackToList={onBackToList}
        componentFields={(state) => <Mqtt defaultState={state} />}
        bodyFormatter={mqttBodyFormatter}
    />
);
