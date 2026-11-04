// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { IPCameraSourceConfig } from '@/api/types';

import { EditSource } from '../deprecated/edit-source/edit-source.component';
import { IpCamera } from '../deprecated/ip-camera/ip-camera.component';
import { ipCameraBodyFormatter } from '../deprecated/ip-camera/utils';
import type { EditSourceProps } from '../types';

export const EditIpCameraSource = ({
    source,
    isConnected,
    onSaved,
    onBackToList,
}: EditSourceProps<IPCameraSourceConfig>) => (
    <EditSource
        config={source}
        isConnected={isConnected}
        onSaved={onSaved}
        onBackToList={onBackToList}
        componentFields={(state) => <IpCamera defaultState={state} />}
        bodyFormatter={ipCameraBodyFormatter}
    />
);
