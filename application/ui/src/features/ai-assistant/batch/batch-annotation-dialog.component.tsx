// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef, useState } from 'react';

import { AssistantSwitcher } from '@/features/ai-assistant/components/assistant-switcher.component';
import { ConnectionSettings } from '@/features/ai-assistant/components/connection-settings.component';
import {
    ActionButton,
    Button,
    ButtonGroup,
    Checkbox,
    Content,
    Dialog,
    Divider,
    Flex,
    Heading,
    InlineAlert,
    Item,
    Picker,
    ProgressBar,
    Text,
    Tooltip,
    TooltipTrigger,
    type Key,
} from '@geti-ui/ui';
import { Gear } from '@geti-ui/ui/icons';
import { useQueryClient } from '@tanstack/react-query';
import { useProject } from 'hooks/api/project.hook';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { useConnectionStatus } from '../hooks/use-connection-status';
import {
    runBatchAnnotation,
    type BatchAnnotationProgress,
    type BatchAnnotationResult,
    type VideoFramesPerSecond,
} from './batch-annotate';

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
    skipped: 0,
    annotationsAdded: 0,
    current: '',
};

const VIDEO_SAMPLING_OPTIONS: { key: string; rate: VideoFramesPerSecond; label: string }[] = [
    { key: '1', rate: 1, label: '1 frame/s (recommended)' },
    { key: '2', rate: 2, label: '2 frames/s' },
    { key: '5', rate: 5, label: '5 frames/s (dense)' },
    { key: '10', rate: 10, label: '10 frames/s (high cost)' },
];

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
    const [onlyUnannotated, setOnlyUnannotated] = useState(false);
    const [videoFramesPerSecond, setVideoFramesPerSecond] = useState<VideoFramesPerSecond>(1);
    const [settingsOpen, setSettingsOpen] = useState(false);
    const isSelection = selectedMediaIds.length > 0;

    useEffect(() => {
        if (!connectionStatus.isLoading && !connectionStatus.isReady) setSettingsOpen(true);
    }, [connectionStatus.isLoading, connectionStatus.isReady]);

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
                onlyUnannotated,
                videoFramesPerSecond,
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
    const isWaitingForFirstResult = progress.phase === 'annotating' && progress.completed === 0;
    const runningSummary = [
        `${progress.succeeded} completed`,
        `${progress.failed} failed`,
        `${progress.skipped} skipped`,
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
                                <Flex alignItems='center' gap='size-100'>
                                    <AssistantSwitcher />
                                    <TooltipTrigger>
                                        <ActionButton
                                            isQuiet
                                            aria-label='Connection settings'
                                            aria-pressed={settingsOpen}
                                            onPress={() => setSettingsOpen((open) => !open)}
                                        >
                                            <Gear />
                                        </ActionButton>
                                        <Tooltip>Connection settings</Tooltip>
                                    </TooltipTrigger>
                                </Flex>
                            </Flex>
                            <Checkbox isSelected={onlyUnannotated} onChange={setOnlyUnannotated}>
                                Only media without annotations
                            </Checkbox>
                            <Flex alignItems='end' gap='size-150'>
                                <Picker
                                    flex={1}
                                    label='Video sampling'
                                    selectedKey={String(videoFramesPerSecond)}
                                    onSelectionChange={(key: Key | null) => {
                                        if (key !== null) {
                                            const option = VIDEO_SAMPLING_OPTIONS.find((item) => item.key === key);
                                            if (option !== undefined) setVideoFramesPerSecond(option.rate);
                                        }
                                    }}
                                >
                                    {VIDEO_SAMPLING_OPTIONS.map(({ key, label }) => (
                                        <Item key={key}>{label}</Item>
                                    ))}
                                </Picker>
                                <Text UNSAFE_className={classes.samplingHint}>
                                    Applies to every video in this run. Higher rates use more API calls.
                                </Text>
                            </Flex>
                            {settingsOpen && <ConnectionSettings status={connectionStatus} />}
                        </>
                    )}

                    {isRunning && (
                        <>
                            <ProgressBar
                                label={progress.phase === 'preparing' ? 'Preparing media' : 'Annotating media'}
                                value={progress.completed}
                                maxValue={total}
                                isIndeterminate={isWaitingForFirstResult}
                                showValueLabel={!isWaitingForFirstResult}
                            />
                            <div className={classes.activityLine}>
                                <span className={classes.activityDot} aria-hidden='true' />
                                <Text UNSAFE_className={classes.currentItem}>{progress.current}</Text>
                            </div>
                            <Text>{runningSummary}</Text>
                        </>
                    )}

                    {result !== null && (
                        <>
                            <Heading level={4} margin={0}>
                                {result.cancelled ? 'Annotation stopped' : 'Annotation complete'}
                            </Heading>
                            <Text>
                                {result.succeeded} completed, {result.skipped} skipped, {result.failed} failed,{' '}
                                {result.annotationsAdded} annotations added
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
