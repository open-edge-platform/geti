// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useMemo } from 'react';

import { ActionButton, DialogTrigger, Flex, Link, ProgressCircle, Text, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { IconColorValue } from '@react-types/shared/src/dna';
import AlertCircle from '@spectrum-icons/workflow/AlertCircle';

import { AcceptCircle, Alert, Image, Play, Refresh } from '../../../../../../assets/icons';
import { COLOR_MODE } from '../../../../../../assets/icons/color-mode.enum';
import { MEDIA_TYPE } from '../../../../../../core/media/base-media.interface';
import {
    ErrorListItem,
    ProgressListItem,
    QueuedListItem,
    SuccessListItem,
} from '../../../../../../providers/media-upload-provider/media-upload.interface';
import { ThinProgressBar } from '../../../../../../shared/components/thin-progress-bar/thin-progress-bar.component';
import { TruncatedTextWithTooltip } from '../../../../../../shared/components/truncated-text/truncated-text.component';
import { getFileSize } from '../../../../../../shared/utils';
import { useDatasetMediaUpload } from '../../../project-dataset/hooks/dataset-media-upload';
import { UploadStatusErrorDialog } from './upload-status-error-dialog.component';

import classes from './upload-status.module.scss';

export enum UploadStatusDialogItemTypes {
    PROGRESS,
    SUCCESS,
    COMMON,
    ERROR,
}

interface UploadStatusDialogItemProps {
    item: SuccessListItem | ErrorListItem | ProgressListItem | QueuedListItem;
    type: UploadStatusDialogItemTypes;
}
export const UploadStatusDialogItem = ({ item, type }: UploadStatusDialogItemProps): JSX.Element => {
    const { retry } = useDatasetMediaUpload();

    const itemProgress = useMemo<number>(() => {
        if (type === UploadStatusDialogItemTypes.COMMON) {
            return 0;
        }
        if (type === UploadStatusDialogItemTypes.PROGRESS) {
            return (item as ProgressListItem).progress;
        }
        return 100;
    }, [type, item]);

    const typeColor = useMemo<IconColorValue>(() => {
        switch (type) {
            case UploadStatusDialogItemTypes.PROGRESS:
            case UploadStatusDialogItemTypes.COMMON:
                return 'informative';
            case UploadStatusDialogItemTypes.SUCCESS:
                return 'positive';
            case UploadStatusDialogItemTypes.ERROR:
                return 'negative';
        }
    }, [type]);

    const isValidationError = useMemo<boolean>(() => {
        if (type !== UploadStatusDialogItemTypes.ERROR) return false;

        const errorItem = item as ErrorListItem;

        return errorItem.status < 0 || errorItem.status === 415;
    }, [type, item]);

    const statusColumnContent = useMemo<JSX.Element>(() => {
        switch (type) {
            case UploadStatusDialogItemTypes.PROGRESS:
            case UploadStatusDialogItemTypes.COMMON:
                return (
                    <ProgressCircle
                        size='S'
                        aria-label='Loading...'
                        value={(item as ProgressListItem).progress}
                        isIndeterminate={
                            !item.hasOwnProperty('progress') ||
                            (item as ProgressListItem).progress === 0 ||
                            (item as ProgressListItem).progress === 100
                        }
                    />
                );
            case UploadStatusDialogItemTypes.SUCCESS:
                return (
                    <AcceptCircle
                        color={COLOR_MODE.POSITIVE}
                        aria-label='upload-success-icon'
                        id={'upload-success-icon'}
                    />
                );
            case UploadStatusDialogItemTypes.ERROR:
                return (
                    <Flex alignItems='center' justifyContent='end' gap='size-100'>
                        <DialogTrigger type='popover'>
                            <>
                                <Link UNSAFE_style={{ width: 'max-content' }}>Error</Link>
                                <Alert color={COLOR_MODE.NEGATIVE} aria-label='alert-icon' />
                            </>
                            <UploadStatusErrorDialog item={item as ErrorListItem} />
                        </DialogTrigger>

                        <TooltipTrigger placement={'bottom'}>
                            <ActionButton
                                isQuiet
                                isDisabled={isValidationError}
                                onPress={() => retry(item as ErrorListItem)}
                            >
                                <Refresh aria-label='progress-icon' />
                            </ActionButton>
                            <Tooltip>Retry</Tooltip>
                        </TooltipTrigger>
                    </Flex>
                );
        }
    }, [type, item, isValidationError, retry]);

    const baseItemIcon = useMemo<JSX.Element>(() => {
        const isImageType = item.fileType.startsWith(MEDIA_TYPE.IMAGE);
        const isVideoType =
            item.fileType.startsWith(MEDIA_TYPE.VIDEO) || item.fileType.startsWith(MEDIA_TYPE.VIDEO_FRAME);

        return isImageType ? (
            <Image width={'100%'} height={'100%'} aria-label='image-icon' />
        ) : isVideoType ? (
            <Play aria-label='play-icon' />
        ) : (
            <AlertCircle size='S' aria-label='alert-circle-icon' />
        );
    }, [item]);

    return (
        <Flex direction='column' marginBottom='size-50' id={`media-item-${item.uploadId}`}>
            <Flex alignItems='center' gap='size-100' flexShrink={1}>
                <View width='size-400' height='size-400' backgroundColor={'gray-200'} borderRadius={'small'}>
                    <Flex
                        width={'100%'}
                        height={'100%'}
                        alignItems={'center'}
                        justifyContent={'center'}
                        UNSAFE_className={classes.itemIconWrapper}
                    >
                        {baseItemIcon}
                    </Flex>
                </View>
                <Flex flex={3} alignItems='center' maxWidth={220}>
                    <TruncatedTextWithTooltip>{item.fileName}</TruncatedTextWithTooltip>
                </Flex>
                <Flex
                    flex={1}
                    alignItems='center'
                    justifyContent='end'
                    UNSAFE_className={[
                        classes.fileSizeWrapper,
                        type === UploadStatusDialogItemTypes.ERROR ? 'error' : '',
                    ].join(' ')}
                >
                    <Text>{getFileSize(item.fileSize)}</Text>
                </Flex>
                <Flex flex={1} alignItems='center' justifyContent='end'>
                    <View
                        paddingEnd={type === UploadStatusDialogItemTypes.ERROR ? 'size-50' : 'size-150'}
                        UNSAFE_className={classes.statusColumnContent}
                    >
                        {statusColumnContent}
                    </View>
                </Flex>
            </Flex>
            <ThinProgressBar size='size-25' color={typeColor} progress={itemProgress} />
        </Flex>
    );
};
