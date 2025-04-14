// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import dayjs from 'dayjs';
import relativeTime from 'dayjs/plugin/relativeTime';
import isEmpty from 'lodash/isEmpty';
import { v4 as uuidv4 } from 'uuid';

import { DatasetIdentifier } from '../../core/projects/dataset.interface';
import { QueuedItem } from '../../shared/concurrent-item-processor/concurrent-item-processor';
import { isVideoFile, loadImageFromFile } from '../../shared/media-utils';
import {
    ErrorListItem,
    MEDIA_CONTENT_BUCKET,
    MediaUploadState,
    ProgressListItem,
    QueuedListItem,
    SuccessListItem,
} from './media-upload.interface';

dayjs.extend(relativeTime);

export const getTotalProgress = (totalHandled: number, totalWaiting: number): number => {
    // Because dividing by zero is not cool
    const totalBeingProcessed = Math.max(1, totalHandled + totalWaiting);

    return Math.round((totalHandled / totalBeingProcessed) * 100);
};

export const getElapsedTimeText = (startTime: number | null): string => {
    if (!startTime) {
        return 'calculating...';
    }

    return `${dayjs(startTime).fromNow(true)} elapsed`;
};

export const getIfUploadStatusBarIsVisible = (
    isUploadInProgress: boolean,
    successList: SuccessListItem[],
    errorList: ErrorListItem[]
): boolean => {
    return isUploadInProgress || !isEmpty(successList) || !isEmpty(errorList);
};

export const convertUploadMediaToMediaUploadItemDTO = (
    datasetIdentifier: DatasetIdentifier,
    file: File,
    labelIds?: string[],
    meta?: MEDIA_CONTENT_BUCKET
): QueuedListItem => {
    const uploadMediaItem: QueuedListItem = {
        uploadId: uuidv4(),
        datasetIdentifier,
        file,
        fileName: file.name,
        fileSize: file.size,
        fileType: file.type,
    };

    if (labelIds) uploadMediaItem.uploadInfo = { filename: file.name, label_ids: labelIds };

    if (meta) {
        return { ...uploadMediaItem, meta };
    }

    return uploadMediaItem;
};

export const getProcessingItems = (
    mediaUploadState: MediaUploadState
): {
    datasetId: string;
    processingQueue: ProgressListItem[];
    waitingQueue: QueuedListItem[];
    successList: SuccessListItem[];
}[] => {
    return Object.keys(mediaUploadState)
        .filter((datasetId) => mediaUploadState[datasetId].isUploadInProgress)
        .map((datasetId) => {
            const datasetUploadState = mediaUploadState[datasetId];

            return {
                datasetId,
                processingQueue: datasetUploadState.processingQueue,
                waitingQueue: datasetUploadState.waitingQueue,
                successList: datasetUploadState.successList,
            };
        });
};

const MAX_CONCURRENCY_LARGE_FILES = 1;
const MAX_CONCURRENCY_MEDIUM_FILES = 5;
const DEFAULT_CONCURRENCY = 10;

const MAX_MEDIUM_SIZE = 3145728; // 3mb
const MAX_LARGE_SIZE = 5242880; // 5mb
const file4KDimensions = { width: 3840, height: 2160 };
const file8KDimensions = { width: 7680, height: 4320 };

export const computeFileUploadConcurrency = async (media: QueuedListItem[]) => {
    let concurrency = DEFAULT_CONCURRENCY;

    if (media.length === 0) {
        return concurrency;
    }

    for (let index = 0; index < media.length; index++) {
        const file = media[index].file;

        if (isVideoFile(file)) {
            concurrency = MAX_CONCURRENCY_LARGE_FILES;

            break;
        }

        try {
            const img = await loadImageFromFile(file);

            if (img.width >= file8KDimensions.width || img.height >= file8KDimensions.height) {
                concurrency = MAX_CONCURRENCY_LARGE_FILES;

                break;
            }

            if (img.width >= file4KDimensions.width || img.height >= file4KDimensions.height) {
                concurrency = MAX_CONCURRENCY_MEDIUM_FILES;

                break;
            }
        } catch {
            if (file.size >= MAX_LARGE_SIZE) {
                concurrency = MAX_CONCURRENCY_LARGE_FILES;
            } else if (file.size >= MAX_MEDIUM_SIZE) {
                concurrency = MAX_CONCURRENCY_MEDIUM_FILES;
            } else {
                concurrency = DEFAULT_CONCURRENCY;
            }

            break;
        }
    }

    return concurrency;
};

const concurrencyLimitForFile = async (file: File) => {
    // If item is large, set max to 1, only add if itemsInQueue + 1 < theMax
    if (isVideoFile(file)) {
        return MAX_CONCURRENCY_LARGE_FILES;
    }

    try {
        const img = await loadImageFromFile(file);

        if (img.width >= file8KDimensions.width || img.height >= file8KDimensions.height) {
            return MAX_CONCURRENCY_LARGE_FILES;
        }

        // If item is medium, set max to 5, only add if itemsInQueue + 1 < theMax
        if (img.width >= file4KDimensions.width || img.height >= file4KDimensions.height) {
            return MAX_CONCURRENCY_MEDIUM_FILES;
        }
    } catch {
        if (file.size >= MAX_LARGE_SIZE) {
            return MAX_CONCURRENCY_LARGE_FILES;
        } else if (file.size >= MAX_MEDIUM_SIZE) {
            return MAX_CONCURRENCY_MEDIUM_FILES;
        }
    }

    return DEFAULT_CONCURRENCY;
};

/**
 * When uploading media to the server we try to do as much in parallel as possible to
 * speed up the upload process. However due to memory issues on the server side we must
 * prevent the browser from uploading multiple large files at the same time.
 * This function aims to solve that problem by:
 * 1. Uploading max MAX_CONCURRENCY_LARGE_FILES video or large images at a time, without any other media
 * 2. If a "medium" sized image is queud then the queue size will be set to MAX_CONCURRENCY_MEDIUM_FILES
 * 3. If no large or medium sized images are queued we process DEFAULT_CONCURRENCY at a time
 */
export const getUploadsToBeRunConcurrently = async (
    mediaUploadsInProcess: QueuedItem<QueuedListItem>[],
    nextMedia: QueuedItem<QueuedListItem>[]
): Promise<QueuedItem<QueuedListItem>[]> => {
    if (mediaUploadsInProcess.length > DEFAULT_CONCURRENCY) {
        return [];
    }

    // The items that we will be processing next
    const output: Array<QueuedItem<QueuedListItem>> = [];
    let concurrencyLimit = DEFAULT_CONCURRENCY;

    // Add items to be processed until we hit the concurrency limit
    for (let amount = 0; amount < concurrencyLimit - mediaUploadsInProcess.length; amount++) {
        const item = nextMedia.at(amount);

        if (!item) {
            continue;
        }

        concurrencyLimit = Math.min(concurrencyLimit, await concurrencyLimitForFile(item.item.file));

        const itemsInQueue = mediaUploadsInProcess.length + output.length;

        if (itemsInQueue > concurrencyLimit) {
            break;
        }

        output.push(item);
    }

    return output;
};
