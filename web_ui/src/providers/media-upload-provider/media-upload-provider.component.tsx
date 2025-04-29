// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { createContext, Dispatch, useContext, useMemo, useReducer, useRef } from 'react';

import dayjs from 'dayjs';
import duration from 'dayjs/plugin/duration';
import relativeTime from 'dayjs/plugin/relativeTime';

import { MissingProviderError } from '../../shared/missing-provider-error';
import { MediaUploadReducer } from './media-upload-reducer';
import { DatasetMediaUploadActions, MediaUploadActionTypes } from './media-upload-reducer-actions';
import {
    ErrorListItem,
    MEDIA_CONTENT_BUCKET,
    MediaUploadItemState,
    MediaUploadProviderProps,
    MediaUploadState,
    ProgressListItem,
    QueuedListItem,
    SuccessListItem,
    UploadMedia,
} from './media-upload.interface';
import { useUploadQueueRef } from './use-upload-queue-ref.hook';
import { convertUploadMediaToMediaUploadItemDTO, getIfUploadStatusBarIsVisible } from './utils';

dayjs.extend(duration);
dayjs.extend(relativeTime);

// The media upload state uses separate lists for keeping track of the queued, in progress,
// errored and successful upload items
// While the intent is for components to only rely on `state` directly, we will keep these
// extra lists as an way to more easily refactor our upload code
const useMediaUploadState = () => {
    const [state, dispatch] = useReducer(MediaUploadReducer, {});

    const mediaUploadState = useMemo(() => {
        return Object.fromEntries(
            Object.keys(state).map((datasetId) => {
                const list = state[datasetId].list;
                const waitingQueue: QueuedListItem[] = [];
                const errorList: ErrorListItem[] = [];
                const successList: SuccessListItem[] = [];
                const processingQueue: ProgressListItem[] = [];
                const progressMap: Record<string, ProgressListItem> = {};
                const uploadProgress = {
                    [MEDIA_CONTENT_BUCKET.ANOMALOUS]: { isUploading: false },
                    [MEDIA_CONTENT_BUCKET.GENERIC]: { isUploading: false },
                    [MEDIA_CONTENT_BUCKET.NORMAL]: { isUploading: false },
                };

                for (const item of list) {
                    switch (item.type) {
                        case MediaUploadItemState.QUEUED: {
                            waitingQueue.push(item);
                            uploadProgress.Generic.isUploading = true;

                            // Potentially set upload progress for anomalous or normal bucket
                            const bucket = item.meta ?? MEDIA_CONTENT_BUCKET.GENERIC;
                            uploadProgress[bucket].isUploading = true;

                            break;
                        }
                        case MediaUploadItemState.PROGRESS: {
                            processingQueue.push(item);
                            progressMap[item.uploadId] = item;
                            uploadProgress.Generic.isUploading = true;

                            // Potentially set upload progress for anomalous or normal bucket
                            const bucket = item.meta ?? MEDIA_CONTENT_BUCKET.GENERIC;
                            uploadProgress[bucket].isUploading = true;
                            break;
                        }
                        case MediaUploadItemState.SUCCESS: {
                            successList.push(item);
                            break;
                        }
                        case MediaUploadItemState.ERROR: {
                            errorList.push(item);
                            break;
                        }
                    }
                }

                const isUploadInProgress = processingQueue.length > 0 || waitingQueue.length > 0;

                const isUploadStatusBarVisible = getIfUploadStatusBarIsVisible(
                    isUploadInProgress,
                    successList,
                    errorList
                );

                return [
                    datasetId,
                    {
                        list: state[datasetId].list,
                        insufficientStorage: state[datasetId].insufficientStorage,
                        timeUploadStarted: state[datasetId].timeUploadStarted,
                        uploadProgress,
                        progressMap,
                        errorList,
                        successList,
                        waitingQueue,
                        processingQueue,
                        isUploadStatusBarVisible,
                        isUploadInProgress,
                    },
                ];
            })
        );
    }, [state]);

    return [mediaUploadState, dispatch] as const;
};

interface MediaUploadContextProps {
    /* If there is any item currently still being processed */
    readonly isUploadInProgress: boolean;

    /* Retries uploading a specific item */
    retryUpload: (datasetId: string) => (errorItem: ErrorListItem) => void;

    /* Removes all elements from the queue of given dataset upload*/
    abortMediaUploads: (datasetId: string) => () => void;

    /* Clears the upload details dialog information */
    reset: (datasetId: string) => () => void;

    /* Triggers and update on the reducer controlling `mediaUploadState` */
    dispatch: Dispatch<DatasetMediaUploadActions>;

    /* Controlled by a reducer, contains the state of the current dataset's upload logic */
    mediaUploadState: MediaUploadState;

    /* Callback to handle media upload */
    onUploadMedia: (datasetId: string) => (uploadMedia: UploadMedia) => Promise<void>;
}

const MediaUploadContext = createContext<MediaUploadContextProps | undefined>(undefined);

export const MediaUploadProvider = ({ children }: MediaUploadProviderProps): JSX.Element => {
    const [mediaUploadState, dispatch] = useMediaUploadState();

    const abortControllers = useRef<Map<string, AbortController>>(new Map());
    const uploadQueue = useUploadQueueRef(dispatch, abortControllers.current);

    const isUploadInProgress = useMemo(
        () => Object.values(mediaUploadState).some(({ isUploadInProgress: isInProgress }) => isInProgress),
        [mediaUploadState]
    );

    const onUploadMedia =
        (datasetId: string) =>
        async (uploadMedia: UploadMedia): Promise<void> => {
            const { datasetIdentifier, files, labelIds, meta } = uploadMedia;

            const uploadItems = files.map((file: File) =>
                convertUploadMediaToMediaUploadItemDTO(datasetIdentifier, file, labelIds, meta)
            );

            dispatch({
                type: MediaUploadActionTypes.ADD_TO_WAITING_QUEUE,
                payload: {
                    items: uploadItems,
                    timeUploadStarted: new Date().getTime(),
                },
                datasetId,
            });

            await Promise.all([...uploadItems].map((item) => uploadQueue.current.addItem(item)));
        };

    const abortMediaUploads = (datasetId: string) => (): void => {
        dispatch({
            type: MediaUploadActionTypes.ABORT_UPLOADS,
            datasetId,
        });

        const abortController = abortControllers.current.get(datasetId);
        if (abortController) {
            abortController.abort();
            abortControllers.current.delete(datasetId);
        }

        uploadQueue.current.clear();
    };

    const retryUpload = () => {
        return async (errorItem: ErrorListItem): Promise<void> => {
            const { file, datasetIdentifier, uploadId, uploadInfo, meta } = errorItem;

            // To reduce memory consumption of the app we remove the reference to the file if the upload
            // finished successfully, since this only happens on a successful run this condition should
            // not be possible
            if (file === undefined) {
                return;
            }

            const media: QueuedListItem = {
                uploadId,
                file,
                fileName: file.name,
                fileSize: file.size,
                fileType: file.type,
                datasetIdentifier,
                uploadInfo,
                meta,
            };

            await uploadQueue.current.addItem(media);
        };
    };

    const reset = (datasetId: string) => (): void => {
        dispatch({ type: MediaUploadActionTypes.RESET, datasetId });
    };

    const value: MediaUploadContextProps = {
        reset,
        dispatch,
        retryUpload,
        onUploadMedia,
        mediaUploadState,
        isUploadInProgress,
        abortMediaUploads,
    };

    return <MediaUploadContext.Provider value={value}>{children}</MediaUploadContext.Provider>;
};

export const useMediaUpload = (): MediaUploadContextProps => {
    const context = useContext(MediaUploadContext);

    if (context === undefined) {
        throw new MissingProviderError('useMediaUpload', 'MediaUploadProvider');
    }

    return context;
};
