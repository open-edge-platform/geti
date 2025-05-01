// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect, useMemo, useRef } from 'react';

import { Flex, ProgressCircle, Text } from '@adobe/react-spectrum';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';
import { ThinProgressBar } from '@shared/components/thin-progress-bar/thin-progress-bar.component';
import { TruncatedTextWithTooltip } from '@shared/components/truncated-text/truncated-text.component';
import { getPlural } from '@shared/utils';

import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import {
    MediaUploadPerDataset,
    UploadMedia,
} from '../../../../../providers/media-upload-provider/media-upload.interface';
import { getElapsedTimeText, getTotalProgress } from '../../../../../providers/media-upload-provider/utils';
import { UploadStatusDialog } from './upload-status-dialog/upload-status-dialog.component';

import classes from './upload-status-bar.module.scss';

interface UploadStatusBarProps {
    reset: () => void;
    abortMediaUploads: () => void;
    mediaUploadState: MediaUploadPerDataset;
    onUploadMedia: (upload: UploadMedia) => Promise<void>;
}

interface LoadingMediasProps {
    progress?: number;
    isIndeterminate?: boolean;
    fileName?: string;
    timeUploadStarted: number | null;
    totalWaiting: number;
    totalProgress: number;
}

const LoadingMedias = ({
    progress,
    fileName,
    totalWaiting,
    totalProgress,
    isIndeterminate,
    timeUploadStarted,
}: LoadingMediasProps) => {
    return (
        <>
            <Flex>
                <Flex flex={5} alignItems='center' justifyContent='start' flexBasis={0} minWidth={0}>
                    <ProgressCircle
                        size='S'
                        marginEnd='size-75'
                        aria-label='Loading…'
                        value={progress}
                        isIndeterminate={isIndeterminate}
                    />
                    <TruncatedTextWithTooltip>{fileName ?? 'Upload pending...'}</TruncatedTextWithTooltip>
                </Flex>

                <Flex flex={3} alignItems='center' justifyContent='center' wrap='nowrap'>
                    <Text UNSAFE_className={classes.timeElapsed}>{getElapsedTimeText(timeUploadStarted)}</Text>
                </Flex>

                <Flex flex={2} alignItems='center' justifyContent='center' wrap='nowrap'>
                    <Text>{`${totalWaiting} ${totalWaiting > 1 ? 'files' : 'file'} left`}</Text>
                </Flex>
            </Flex>
            <ThinProgressBar
                left={0}
                bottom={-2}
                trackColor='gray-600'
                progress={totalProgress}
                position={'absolute'}
            />
        </>
    );
};
export const UploadStatusBar = ({
    reset,
    onUploadMedia,
    abortMediaUploads,
    mediaUploadState,
}: UploadStatusBarProps): JSX.Element => {
    const loadedMediasRef = useRef('');
    const loadingMediasRef = useRef('');
    const { addNotification, removeNotification } = useNotification();
    const uploadStatusDialogState = useOverlayTriggerState({});

    const { processingQueue, timeUploadStarted, successList, errorList, isUploadInProgress, isUploadStatusBarVisible } =
        mediaUploadState;

    const [totalWaiting, totalProgress] = useMemo(() => {
        const handled = mediaUploadState.successList.length + mediaUploadState.errorList.length;
        const waiting = mediaUploadState.waitingQueue.length + mediaUploadState.processingQueue.length;

        return [waiting, getTotalProgress(handled, waiting)];
    }, [mediaUploadState]);

    const errorMessage = errorList.length > 0 ? ` - ${errorList.length} ${`error${getPlural(errorList.length)}`}` : '';

    const total = successList.length + errorList.length;
    const resultMessage = `Uploaded ${successList.length} of ${total} ${`file${getPlural(total)}`}${errorMessage}`;

    useEffect(() => {
        if (!isUploadStatusBarVisible) {
            removeNotification(loadingMediasRef.current);
            removeNotification(loadedMediasRef.current);
            return;
        }

        if (!isUploadInProgress) {
            removeNotification(loadingMediasRef.current);

            loadedMediasRef.current = addNotification({
                onClose: () => {
                    reset();
                    uploadStatusDialogState.close();
                },
                message: resultMessage,
                type: NOTIFICATION_TYPE.DEFAULT,
                dismiss: { duration: 0, click: false, touch: false },
                actionButtons: [
                    <QuietActionButton
                        key={'status-dialog'}
                        onPress={uploadStatusDialogState.open}
                        UNSAFE_style={{ textDecoration: 'underline' }}
                    >
                        Details
                    </QuietActionButton>,
                ],
            });
        }

        if (isUploadInProgress) {
            removeNotification(loadedMediasRef.current);
            loadingMediasRef.current = addNotification({
                hasCloseButton: false,
                message: (
                    <LoadingMedias
                        key={'loading-medias'}
                        totalProgress={totalProgress}
                        totalWaiting={totalWaiting}
                        timeUploadStarted={timeUploadStarted}
                        fileName={processingQueue[0]?.fileName}
                        progress={processingQueue[0]?.progress}
                        isIndeterminate={!processingQueue[0]?.progress || processingQueue[0]?.progress === 100}
                    />
                ),
                actionButtons: [
                    <QuietActionButton
                        key={'status-dialog'}
                        onPress={uploadStatusDialogState.open}
                        UNSAFE_style={{ textDecoration: 'underline' }}
                    >
                        Details
                    </QuietActionButton>,
                ],
                type: NOTIFICATION_TYPE.DEFAULT,
                dismiss: { duration: 0, click: false, touch: false },
            });
        }
    }, [
        reset,
        removeNotification,
        addNotification,
        isUploadInProgress,
        isUploadStatusBarVisible,
        processingQueue,
        resultMessage,
        timeUploadStarted,
        totalProgress,
        totalWaiting,
        uploadStatusDialogState,
    ]);

    return (
        <UploadStatusDialog
            isUploadInProgress={mediaUploadState.isUploadInProgress}
            abortMediaUploads={abortMediaUploads}
            isOpen={uploadStatusDialogState.isOpen}
            onClose={uploadStatusDialogState.close}
            onUploadMedia={onUploadMedia}
        />
    );
};
