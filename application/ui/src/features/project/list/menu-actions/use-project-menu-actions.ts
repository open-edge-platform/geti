// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Key } from '@geti-ui/ui';
import { useIsPipelineConfigured } from 'hooks/use-is-pipeline-configured.hook';
import { useTranslation } from 'react-i18next';

import { toast } from '../../../../components/toast/toast.component';
import { useDisablePipeline, useEnablePipeline, useProjectPipeline } from '../../../../hooks/api/pipeline.hook';

type ProjectMenuCallbacks = {
    onRename: () => void;
    onDelete: () => void;
    onEnableBlocked: () => void;
};

type MenuAction = {
    key: string;
    label: string;
};

export const useProjectMenuActions = (
    projectId: string,
    callbacks: ProjectMenuCallbacks,
    isPipelineRunning?: boolean
) => {
    const enablePipelineMutation = useEnablePipeline();
    const disablePipelineMutation = useDisablePipeline();
    const projectPipelineQuery = useProjectPipeline(projectId);
    const { t } = useTranslation();

    const isPipelineConfigured = useIsPipelineConfigured(projectPipelineQuery.data);

    const menuActions: MenuAction[] = [
        ...(isPipelineRunning
            ? [{ key: 'disable-pipeline', label: t('projectPanel.disablePipeline') }]
            : [{ key: 'enable-pipeline', label: t('projectPanel.enablePipeline') }]),
        { key: 'rename', label: t('projectPanel.rename') },
        { key: 'delete', label: t('projectPanel.delete') },
    ];

    const handleAction = (key: Key) => {
        const mutationParams = { params: { path: { project_id: projectId } } };

        switch (key) {
            case 'enable-pipeline':
                if (!isPipelineConfigured) {
                    callbacks.onEnableBlocked();
                    return;
                }

                enablePipelineMutation.mutate(mutationParams, {
                    onSuccess: () => {
                        toast({ type: 'success', message: t('projectPanel.pipelineEnabledToast') });
                    },
                });
                break;
            case 'disable-pipeline':
                disablePipelineMutation.mutate(mutationParams, {
                    onSuccess: () => {
                        toast({ type: 'success', message: t('projectPanel.pipelineDisabledToast') });
                    },
                });
                break;
            case 'rename':
                callbacks.onRename();
                break;
            case 'delete':
                callbacks.onDelete();
                break;
            default:
                break;
        }
    };

    return {
        menuActions,
        handleAction,
    };
};
