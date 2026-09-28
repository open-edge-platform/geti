// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useEffect, useRef, useState } from 'react';

import { AssistantSwitcher } from '@/features/ai-assistant/components/assistant-switcher.component';
import { ConnectionSettings } from '@/features/ai-assistant/components/connection-settings.component';
import { useTranslation } from '@/i18n';
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

type VideoSamplingLabelKey =
    | 'assistant.videoSamplingOption1'
    | 'assistant.videoSamplingOption2'
    | 'assistant.videoSamplingOption5'
    | 'assistant.videoSamplingOption10';

const VIDEO_SAMPLING_OPTIONS: { key: string; rate: VideoFramesPerSecond; labelKey: VideoSamplingLabelKey }[] = [
    { key: '1', rate: 1, labelKey: 'assistant.videoSamplingOption1' },
    { key: '2', rate: 2, labelKey: 'assistant.videoSamplingOption2' },
    { key: '5', rate: 5, labelKey: 'assistant.videoSamplingOption5' },
    { key: '10', rate: 10, labelKey: 'assistant.videoSamplingOption10' },
];

export const BatchAnnotationDialog = ({
    selectedMediaIds,
    resolveAllMediaIds,
    onClose,
}: BatchAnnotationDialogProps) => {
    const { t } = useTranslation();
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
            if (resolvedIds === null) throw new Error(t('assistant.filtersChanged'));
            if (resolvedIds.length === 0) throw new Error(t('assistant.noMedia'));
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
            setError(reason instanceof Error ? reason.message : t('assistant.startFailed'));
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
    const runSummary = (value: { succeeded: number; failed: number; skipped: number; annotationsAdded: number }) =>
        t('assistant.runSummary', {
            succeeded: value.succeeded,
            failed: value.failed,
            skipped: value.skipped,
            annotationsAdded: value.annotationsAdded,
        });

    return (
        <Dialog width={640} minHeight={400}>
            <Heading>{t('assistant.title')}</Heading>
            <Divider />
            <Content>
                <Flex direction='column' gap='size-200'>
                    {!isRunning && result === null && (
                        <>
                            <Flex alignItems='center' justifyContent='space-between' gap='size-200'>
                                <Text>
                                    {isSelection
                                        ? t('assistant.selectedMediaCount', { count: selectedMediaIds.length })
                                        : t('assistant.currentFilteredDataset')}
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
                                        <Tooltip>{t('assistant.connectionSettings')}</Tooltip>
                                    </TooltipTrigger>
                                </Flex>
                            </Flex>
                            <Checkbox isSelected={onlyUnannotated} onChange={setOnlyUnannotated}>
                                {t('assistant.onlyUnannotated')}
                            </Checkbox>
                            <Flex alignItems='end' gap='size-150'>
                                <Picker
                                    flex={1}
                                    label={t('assistant.videoSampling')}
                                    selectedKey={String(videoFramesPerSecond)}
                                    onSelectionChange={(key: Key | null) => {
                                        if (key !== null) {
                                            const option = VIDEO_SAMPLING_OPTIONS.find((item) => item.key === key);
                                            if (option !== undefined) setVideoFramesPerSecond(option.rate);
                                        }
                                    }}
                                >
                                    {VIDEO_SAMPLING_OPTIONS.map(({ key, labelKey }) => (
                                        <Item key={key}>{t(labelKey)}</Item>
                                    ))}
                                </Picker>
                                <Text UNSAFE_className={classes.samplingHint}>{t('assistant.videoSamplingHint')}</Text>
                            </Flex>
                            {settingsOpen && <ConnectionSettings status={connectionStatus} />}
                        </>
                    )}

                    {isRunning && (
                        <>
                            <ProgressBar
                                label={
                                    progress.phase === 'preparing'
                                        ? t('assistant.preparingMedia')
                                        : t('assistant.annotatingMedia')
                                }
                                value={progress.completed}
                                maxValue={total}
                                isIndeterminate={isWaitingForFirstResult}
                                showValueLabel={!isWaitingForFirstResult}
                            />
                            <div className={classes.activityLine}>
                                <span className={classes.activityDot} aria-hidden='true' />
                                <Text UNSAFE_className={classes.currentItem}>{progress.current}</Text>
                            </div>
                            <Text>
                                {runSummary({
                                    succeeded: progress.succeeded,
                                    failed: progress.failed,
                                    skipped: progress.skipped,
                                    annotationsAdded: progress.annotationsAdded,
                                })}
                            </Text>
                        </>
                    )}

                    {result !== null && (
                        <>
                            <Heading level={4} margin={0}>
                                {result.cancelled ? t('assistant.runStopped') : t('assistant.runComplete')}
                            </Heading>
                            <Text>
                                {runSummary({
                                    succeeded: result.succeeded,
                                    failed: result.failed,
                                    skipped: result.skipped,
                                    annotationsAdded: result.annotationsAdded,
                                })}
                            </Text>
                            {result.failures.length > 0 && (
                                <div className={classes.failures}>
                                    {result.failures.slice(0, 5).map((failure) => (
                                        <div key={failure.key}>
                                            <strong>{failure.name}</strong>
                                            <span>{failure.message}</span>
                                        </div>
                                    ))}
                                    {result.failures.length > 5 && (
                                        <div className={classes.failureMore}>
                                            {t('assistant.moreFailures', { count: result.failures.length - 5 })}
                                        </div>
                                    )}
                                </div>
                            )}
                        </>
                    )}

                    {error !== null && (
                        <InlineAlert variant='negative' width='100%'>
                            <Heading>{t('assistant.runFailed')}</Heading>
                            <Content>{error}</Content>
                        </InlineAlert>
                    )}
                </Flex>
            </Content>
            <ButtonGroup>
                {isRunning ? (
                    <Button variant='secondary' onPress={() => controller.current?.abort()}>
                        {t('common.actions.cancel')}
                    </Button>
                ) : result !== null ? (
                    <>
                        <Button variant='secondary' onPress={close}>
                            {t('common.actions.close')}
                        </Button>
                        <Button
                            variant='accent'
                            onPress={start}
                            isDisabled={
                                !connectionStatus.isReady || connectionStatus.isLoading || project === undefined
                            }
                        >
                            {t('assistant.runAgain')}
                        </Button>
                    </>
                ) : (
                    <>
                        <Button variant='secondary' onPress={close}>
                            {t('common.actions.cancel')}
                        </Button>
                        <Button
                            variant='accent'
                            onPress={start}
                            isDisabled={
                                !connectionStatus.isReady || connectionStatus.isLoading || project === undefined
                            }
                        >
                            {t('assistant.startAnnotation')}
                        </Button>
                    </>
                )}
            </ButtonGroup>
        </Dialog>
    );
};
