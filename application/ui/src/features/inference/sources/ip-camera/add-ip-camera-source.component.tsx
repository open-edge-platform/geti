// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useTranslation } from '@/i18n';

import { AddSource } from '../deprecated/add-source/add-source.component';
import { IpCamera } from '../deprecated/ip-camera/ip-camera.component';
import { getIpCameraInitialConfig, ipCameraBodyFormatter } from '../deprecated/ip-camera/utils';
import type { AddSourceProps } from '../types';

export const AddIpCameraSource = ({ existingNames, onSaved }: AddSourceProps) => {
    const { t } = useTranslation();

    return (
        <AddSource
            onSaved={onSaved}
            config={getIpCameraInitialConfig(t, existingNames)}
            componentFields={(state) => <IpCamera defaultState={state} />}
            bodyFormatter={ipCameraBodyFormatter}
        />
    );
};
