// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { AddSink } from '../deprecated/add-sink/add-sink.component';
import { Mqtt } from '../deprecated/mqtt/mqtt.component';
import { getMqttInitialConfig, mqttBodyFormatter } from '../deprecated/mqtt/utils';
import type { AddSinkProps } from '../types';

export const AddMqttSink = ({ onSaved }: AddSinkProps) => (
    <AddSink
        onSaved={onSaved}
        config={getMqttInitialConfig()}
        componentFields={(state) => <Mqtt defaultState={state} />}
        bodyFormatter={mqttBodyFormatter}
    />
);
