// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef, useState } from 'react';

import { AssistantSwitcher } from '@/features/ai-assistant/components/assistant-switcher.component';
import { ConnectionSettings } from '@/features/ai-assistant/components/connection-settings.component';
import {
    Button,
    ButtonGroup,
    Content,
    Dialog,
    Divider,
    Flex,
    Heading,
    InlineAlert,
    ProgressBar,
    Text,
} from '@geti-ui/ui';
import { useQueryClient } from '@tanstack/react-query';
import { useProject } from 'hooks/api/project.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { useConnectionStatus } from '../hooks/use-connection-status';
import { runBatchAnnotation, type BatchAnnotationProgress, type BatchAnnotationResult } from './batch-annotate';

import classes from './batch-annotation-dialog.module.scss';

interface BatchAnnotationDialogProps {
    selectedMediaIds: string[];
    resolveAllMediaIds: () => Promise<string[] | null>;
    onClose: () => void;
}

const initialProgress: BatchAnnotationProgress = {
    phase: 'preparing',
    completed: 0,
    total: 0,
    succeeded: 0,
    failed: 0,
    annotationsAdded: 0,
    current: '',
};

export const BatchAnnotationDialog = ({
    selectedMediaIds,
    resolveAllMediaIds,
    onClose,
}: BatchAnnotationDialogProps) => {
    const projectId = useProjectIdentifier();
    const { data: project } = useProject();
    const queryClient = useQueryClient();
    const connectionStatus = useConnectionStatus();
    const controller = useRef<AbortController | null>(null);
    const [isRunning, setIsRunning] = useState(false);
    const [progress, setProgress] = useState(initialProgress);
    const [result, setResult] = useState<BatchAnnotationResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const isSelection = selectedMediaIds.length > 0;

    useEffect(
        () => () => {
            controller.current?.abort();
        },
        []
    );

    const invalidateDatasetQueries = async () => {
        await Promise.all([
            queryClient.invalidateQueries({
                queryKey: ['get', '/api/projects/{project_id}/dataset/items'],
            }),
            queryClient.invalidateQueries({
                queryKey: ['get', '/api/projects/{project_id}/dataset/media'],
            }),
            queryClient.invalidateQueries({
                queryKey: ['get', '/api/projects/{project_id}/dataset/media/{media_id}/annotations'],
            }),
        ]);
    };

    const start = async () => {
        const nextController = new AbortController();
        controller.current = nextController;
        setIsRunning(true);
        setResult(null);
        setError(null);
        setProgress(initialProgress);

        try {
            const resolvedIds = isSelection ? selectedMediaIds : await resolveAllMediaIds();
            if (resolvedIds === null) throw new Error('Dataset filters changed. Start the annotation run again.');
            if (resolvedIds.length === 0) throw new Error('There is no media to annotate.');
            const batchResult = await runBatchAnnotation({
                projectId,
                project,
                mediaIds: resolvedIds,
                signal: nextController.signal,
                onProgress: setProgress,
            });
            setResult(batchResult);
            if (batchResult.completed > 0) await invalidateDatasetQueries();
        } catch (reason) {
            setError(reason instanceof Error ? reason.message : 'The annotation run could not be started.');
        } finally {
            controller.current = null;
            setIsRunning(false);
        }
    };

    const close = () => {
        controller.current?.abort();
        onClose();
    };

    const total = Math.max(progress.total, 1);
    const runningSummary = [
        `${progress.succeeded} completed`,
        `${progress.failed} failed`,
        `${progress.annotationsAdded} annotations added`,
    ].join(', ');

    return (
        <Dialog width={640} minHeight={400}>
            <Heading>Annotate with AI</Heading>
            <Divider />
            <Content>
                <Flex direction='column' gap='size-200'>
                    {!isRunning && result === null && (
                        <>
                            <Flex alignItems='center' justifyContent='space-between' gap='size-200'>
                                <Text>
                                    {isSelection
                                        ? `${selectedMediaIds.length} selected media`
                                        : 'Current filtered dataset'}
                                </Text>
                                <AssistantSwitcher />
                            </Flex>
                            <ConnectionSettings status={connectionStatus} />
                        </>
                    )}

                    {isRunning && (
                        <>
                            <ProgressBar
                                label={progress.phase === 'preparing' ? 'Preparing media' : 'Annotating media'}
                                value={progress.completed}
                                maxValue={total}
                                showValueLabel
                            />
                            <Text UNSAFE_className={classes.currentItem}>{progress.current}</Text>
                            <Text>{runningSummary}</Text>
                        </>
                    )}

                    {result !== null && (
                        <>
                            <Heading level={4} margin={0}>
                                {result.cancelled ? 'Annotation stopped' : 'Annotation complete'}
                            </Heading>
                            <Text>
                                {result.succeeded} completed, {result.failed} failed, {result.annotationsAdded}{' '}
                                annotations added
                            </Text>
                            {result.failures.length > 0 && (
                                <div className={classes.failures}>
                                    {result.failures.slice(0, 5).map((failure) => (
                                        <div key={failure.key}>
                                            <strong>{failure.name}</strong>
                                            <span>{failure.message}</span>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </>
                    )}

                    {error !== null && (
                        <InlineAlert variant='negative' width='100%'>
                            <Heading>Annotation failed</Heading>
                            <Content>{error}</Content>
                        </InlineAlert>
                    )}
                </Flex>
            </Content>
            <ButtonGroup>
                {isRunning ? (
                    <Button variant='secondary' onPress={() => controller.current?.abort()}>
                        Cancel
                    </Button>
                ) : result !== null ? (
                    <Button variant='accent' onPress={close}>
                        Close
                    </Button>
                ) : (
                    <>
                        <Button variant='secondary' onPress={close}>
                            Cancel
                        </Button>
                        <Button
                            variant='accent'
                            onPress={start}
                            isDisabled={!connectionStatus.isReady || connectionStatus.isLoading}
                        >
                            Start annotation
                        </Button>
                    </>
                )}
            </ButtonGroup>
        </Dialog>
    );
};
