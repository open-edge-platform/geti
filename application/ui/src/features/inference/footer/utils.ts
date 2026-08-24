// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { PipelineComponentsHealth, PipelineStatus } from '@/api/types';
import type { StatusLightProps } from '@geti-ui/ui';
import { capitalize } from 'lodash-es';

import { i18n } from '../../../i18n';

export type StatusVariant = StatusLightProps['variant'];

export type ComponentStatusMeta = {
    label: string;
    variant: StatusVariant;
    message: string | null | undefined;
};

export type StatusMeta = {
    label: string;
    variant: StatusVariant;
};

export const getOverallStatusMeta = (status: string): StatusMeta => {
    switch (status) {
        case 'running':
            return { label: i18n.t('inference.statusRunning'), variant: 'positive' };
        case 'idle':
            return { label: i18n.t('inference.statusIdle'), variant: 'neutral' };
        case 'error':
            return { label: i18n.t('inference.statusProblemsDetected'), variant: 'negative' };
        default:
            return { label: capitalize(status), variant: 'neutral' };
    }
};

export const getComponentStatusMeta = (component: PipelineStatus): ComponentStatusMeta => {
    switch (component.status) {
        case 'ok':
            return { label: i18n.t('inference.statusHealthy'), variant: 'positive', message: component.message };
        case 'finished':
            return { label: i18n.t('inference.statusFinished'), variant: 'info', message: component.message };
        case 'unavailable':
            return { label: i18n.t('inference.statusUnavailable'), variant: 'neutral', message: component.message };
        case 'error':
            return { label: i18n.t('inference.statusError'), variant: 'negative', message: component.message };
        default:
            return { label: capitalize(component.status), variant: 'neutral', message: component.message };
    }
};

export const shouldShowPipelineHealthDetails = (components: PipelineComponentsHealth | null | undefined): boolean => {
    if (components == null) {
        return false;
    }

    return [components.source, components.sink, components.model].some((component) => component.message != null);
};
