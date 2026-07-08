// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { StatusLightProps } from '@geti-ui/ui';
import { capitalize } from 'lodash-es';

import { PipelineComponentsHealth, PipelineStatus } from '../../../constants/shared-types';

export type StatusVariant = StatusLightProps['variant'];

export interface StatusMeta {
    label: string;
    variant: StatusVariant;
}

export const getOverallStatusMeta = (status: string): StatusMeta => {
    switch (status) {
        case 'running':
            return { label: 'Running', variant: 'positive' };
        case 'idle':
            return { label: 'Idle', variant: 'neutral' };
        case 'error':
            return { label: 'Problems detected', variant: 'negative' };
        default:
            return { label: capitalize(status), variant: 'neutral' };
    }
};

export const getComponentStatusMeta = (component: PipelineStatus): StatusMeta => {
    if (component.message != null) {
        return { label: component.message, variant: 'negative' };
    }

    switch (component.status) {
        case 'ok':
            return { label: 'Healthy', variant: 'positive' };
        case 'finished':
            return { label: 'Finished', variant: 'info' };
        case 'unavailable':
            return { label: 'Unavailable', variant: 'neutral' };
        case 'error':
            return { label: 'Error', variant: 'negative' };
        default:
            return { label: capitalize(component.status), variant: 'neutral' };
    }
};

export const hasComponentMessage = (components: PipelineComponentsHealth | null | undefined): boolean => {
    if (components == null) {
        return false;
    }

    return [components.source, components.sink, components.model].some((component) => component.message != null);
};
