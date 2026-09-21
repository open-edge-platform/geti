// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useMemo, useState } from 'react';

import { $api } from '@/api';
import { toast } from '@/components/toast/toast.component';
import { Button, ButtonGroup, Content, Dialog, Divider, Flex, Footer, Heading, Item, Picker, Text } from '@geti-ui/ui';
import { useQueryClient } from '@tanstack/react-query';
import { useStreamJobDetail, useSubmitJob } from 'hooks/api/jobs/jobs.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { getQueryKey } from '../../../query-client/query-client';
import { useGetTaskModelArchitectures } from '../../models/hooks/api/use-get-model-architectures.hook';
import { runChatGptAutoLabel } from './chatgpt-auto-label';

import classes from './auto-label-dialog.module.scss';

type AutoLabelMode = 'pretrained' | 'chatgpt';

interface AutoLabelDialogProps {
    onClose: () => void;
    isChatGptAvailable: boolean;
}

export const AutoLabelDialog = ({ onClose, isChatGptAvailable }: AutoLabelDialogProps) => {
    const projectId = useProjectIdentifier();
    const { modelArchitectures } = useGetTaskModelArchitectures();
    const mutation = useSubmitJob();
    const queryClient = useQueryClient();
    const [mode, setMode] = useState<AutoLabelMode>('pretrained');
    const pretrainedModels = useMemo(
        () => modelArchitectures.filter(({ pretrained_auto_label }) => pretrained_auto_label),
        [modelArchitectures]
    );
    const [modelId, setModelId] = useState<string | null>(pretrainedModels.at(0)?.id ?? null);
    const [chatGptProgress, setChatGptProgress] = useState<string | null>(null);
    const [isChatGptRunning, setIsChatGptRunning] = useState(false);
    const [pretrainedJobId, setPretrainedJobId] = useState<string | null>(null);
    useStreamJobDetail(pretrainedJobId);
    const pretrainedJob = $api.useQuery(
        'get',
        '/api/jobs/{job_id}',
        { params: { path: { job_id: pretrainedJobId ?? '00000000-0000-0000-0000-000000000000' } } },
        { enabled: pretrainedJobId !== null }
    );

    useEffect(() => {
        if (pretrainedJob.data?.status !== 'DONE') return;
        void queryClient.invalidateQueries({
            queryKey: getQueryKey([
                'get',
                '/api/projects/{project_id}',
                { params: { path: { project_id: projectId } } },
            ]),
        });
        void queryClient.invalidateQueries({ queryKey: ['get', '/api/projects/{project_id}/dataset/media'] });
        toast({ type: 'success', message: pretrainedJob.data.message ?? 'Pretrained Auto-Label completed.' });
        onClose();
    }, [onClose, pretrainedJob.data?.message, pretrainedJob.data?.status, projectId, queryClient]);

    const start = () => {
        if (mode === 'chatgpt') {
            setIsChatGptRunning(true);
            void runChatGptAutoLabel(projectId, setChatGptProgress)
                .then((result) => {
                    void queryClient.invalidateQueries({
                        queryKey: getQueryKey([
                            'get',
                            '/api/projects/{project_id}',
                            { params: { path: { project_id: projectId } } },
                        ]),
                    });
                    void queryClient.invalidateQueries({
                        queryKey: ['get', '/api/projects/{project_id}/dataset/media'],
                    });
                    toast({
                        type: 'success',
                        message:
                            `ChatGPT selected ${result.selected} images and prepared ` +
                            `${result.annotations} annotations for review.`,
                    });
                    onClose();
                })
                .catch((error: unknown) => {
                    toast({
                        type: 'error',
                        message: error instanceof Error ? error.message : 'ChatGPT Auto-Label failed.',
                    });
                })
                .finally(() => setIsChatGptRunning(false));
            return;
        }
        if (modelId === null) return;
        mutation.mutate(
            {
                body: {
                    job_type: 'pretrained_auto_label',
                    project_id: projectId,
                    parameters: { model_architecture_id: modelId, confidence_threshold: 0.25 },
                },
            },
            {
                onSuccess: (job) => setPretrainedJobId(job.job_id),
            }
        );
    };

    return (
        <Dialog width='clamp(720px, 55vw, 980px)'>
            <Heading>Auto-Label</Heading>
            <Divider size='S' />
            <Content>
                <Flex direction='column' gap='size-300'>
                    <Text>Choose how Geti should create editable pre-labels for this dataset.</Text>
                    <Flex gap='size-200'>
                        <button
                            type='button'
                            className={`${classes.modeCard} ${mode === 'pretrained' ? classes.selected : ''}`}
                            onClick={() => setMode('pretrained')}
                        >
                            <Heading level={3}>Pretrained Auto-Label</Heading>
                            <Text>
                                Run a compatible pretrained model with its original classes. New detected classes become
                                project labels.
                            </Text>
                        </button>
                        <button
                            type='button'
                            className={`${classes.modeCard} ${mode === 'chatgpt' ? classes.selected : ''}`}
                            onClick={() => isChatGptAvailable && setMode('chatgpt')}
                            disabled={!isChatGptAvailable}
                        >
                            <Heading level={3}>ChatGPT</Heading>
                            <Text>
                                Let ChatGPT choose representative dataset images and prepare pre-labels while limiting
                                token use.
                            </Text>
                        </button>
                    </Flex>

                    {mode === 'pretrained' && (
                        <Picker
                            label='Pretrained model'
                            width='100%'
                            items={pretrainedModels}
                            selectedKey={modelId}
                            onSelectionChange={(key) => setModelId(key === null ? null : String(key))}
                        >
                            {(architecture) => (
                                <Item key={architecture.id} textValue={architecture.name}>
                                    {architecture.name} · {architecture.pretrained_dataset}
                                </Item>
                            )}
                        </Picker>
                    )}
                    {mode === 'pretrained' && pretrainedModels.length === 0 && (
                        <Text>No pretrained auto-label model is available for this project type.</Text>
                    )}
                    {mode === 'chatgpt' && chatGptProgress !== null && <Text>{chatGptProgress}</Text>}
                    {pretrainedJobId !== null && pretrainedJob.data !== undefined && (
                        <Text>
                            {pretrainedJob.data.message ?? 'Preparing pretrained model…'} (
                            {Math.round(pretrainedJob.data.progress)}%)
                        </Text>
                    )}
                    {pretrainedJob.data?.status === 'FAILED' && <Text>{pretrainedJob.data.error}</Text>}
                </Flex>
            </Content>
            <Divider size='S' />
            <Footer>
                <ButtonGroup marginStart='auto'>
                    <Button variant='secondary' onPress={onClose}>
                        Cancel
                    </Button>
                    <Button
                        variant='accent'
                        onPress={start}
                        isPending={mutation.isPending || isChatGptRunning}
                        isDisabled={
                            mutation.isPending ||
                            isChatGptRunning ||
                            pretrainedJobId !== null ||
                            (mode === 'pretrained' && modelId === null) ||
                            (mode === 'chatgpt' && !isChatGptAvailable)
                        }
                    >
                        Start Auto-Label
                    </Button>
                </ButtonGroup>
            </Footer>
        </Dialog>
    );
};
