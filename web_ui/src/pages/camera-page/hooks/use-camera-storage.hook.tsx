// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { isVideoFile, loadImageFromFile, loadVideoFromFile } from '@shared/media-utils';
import { useQuery, useQueryClient, UseQueryResult } from '@tanstack/react-query';
import isNil from 'lodash/isNil';
import { useParams } from 'react-router-dom';

import { NOTIFICATION_TYPE } from '../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../notification/notification.component';
import { assertIsNotNullable } from '../../../types-utils/utils';
import { Screenshot } from '../../camera-support/camera.interface';
import { useCameraParams } from './camera-params.hook';
import { useLoadCameraWebworker } from './use-load-camera-webworker';

const CAMERA_DATASET_MEDIA_ITEMS = (projectId: string, datasetId: string, isLivePrediction: boolean) => {
    const key = ['camera-items', projectId, datasetId] as const;

    if (isLivePrediction) {
        return [...key, 'live-prediction'] as const;
    }

    return key;
};

export interface UseCameraStorage {
    savedFilesQuery: UseQueryResult<Screenshot[]>;
    deleteAllItems: (invalidateQuery?: boolean) => Promise<void>;
    deleteMany: (ids: string[]) => Promise<void>;
    saveMedia: (item: Omit<Screenshot, 'file'>) => Promise<void>;
    invalidateCameraStorageQuery: () => Promise<void>;
    updateMany: (
        ids: string[],
        screenshot: Omit<Partial<Screenshot>, 'id'>
    ) => Promise<PromiseSettledResult<void | '' | undefined>[]>;
}

const useSavedFilesQuery = () => {
    const { worker: cameraWorker } = useLoadCameraWebworker();
    const { projectId, datasetId } = useParams<{ projectId: string; datasetId: string }>();
    const { isLivePrediction } = useCameraParams();

    const queryFn = async () => {
        assertIsNotNullable(cameraWorker);

        const mediaItems = await cameraWorker.getItems();

        return Promise.all(
            mediaItems.map(async (media) => {
                const elementLoader = isVideoFile(media.file) ? loadVideoFromFile : loadImageFromFile;
                const element = await elementLoader(media.file);

                return { ...media, dataUrl: element.src };
            })
        );
    };

    return useQuery<Required<Screenshot[]>>({
        queryKey: CAMERA_DATASET_MEDIA_ITEMS(String(projectId), String(datasetId), isLivePrediction),
        queryFn,
        enabled: cameraWorker !== null,
    });
};

export const useCameraStorage = (): UseCameraStorage => {
    const queryClient = useQueryClient();
    const { worker: cameraWorker } = useLoadCameraWebworker();
    const { addNotification } = useNotification();
    const { isLivePrediction } = useCameraParams();
    const { projectId, datasetId } = useParams<{ projectId: string; datasetId: string }>();

    const savedFilesQuery = useSavedFilesQuery();

    const getInvalidateOrEmptyPromise = (invalidateQuery: boolean) => () =>
        invalidateQuery ? invalidateCameraStorageQuery() : Promise.resolve();

    const deleteMany = async (ids: string[]) => {
        return Promise.allSettled(ids.map((id) => cameraWorker?.removeItem(id))).then(invalidateCameraStorageQuery);
    };

    const deleteAllItems = async (invalidateQuery = true) => {
        return cameraWorker?.clear().then(getInvalidateOrEmptyPromise(invalidateQuery));
    };

    const saveMedia = async (screenshot: Omit<Screenshot, 'file'>) => {
        assertIsNotNullable(cameraWorker);

        try {
            await cameraWorker.setItem(screenshot.id, screenshot);
            await invalidateCameraStorageQuery();
        } catch (error: unknown) {
            addNotification({ message: String(error), type: NOTIFICATION_TYPE.ERROR });
        }
    };

    const getMedia = async (id: string) => {
        return cameraWorker?.getItem<Screenshot>(id);
    };

    const updateMany = async (ids: string[], screenshot: Omit<Partial<Screenshot>, 'id'>) => {
        return Promise.allSettled(
            ids.map(async (id) => {
                assertIsNotNullable(cameraWorker);

                const currentData = await getMedia(id);

                if (isNil(currentData)) {
                    return '';
                }

                try {
                    await cameraWorker.updateMedia(id, { ...currentData, ...screenshot });
                    await invalidateCameraStorageQuery();
                } catch (error: unknown) {
                    addNotification({ message: String(error), type: NOTIFICATION_TYPE.ERROR });
                }
            })
        );
    };

    const invalidateCameraStorageQuery = () => {
        return queryClient.invalidateQueries({
            queryKey: CAMERA_DATASET_MEDIA_ITEMS(String(projectId), String(datasetId), isLivePrediction),
        });
    };

    return {
        savedFilesQuery,
        saveMedia,
        updateMany,
        deleteMany,
        deleteAllItems,
        invalidateCameraStorageQuery,
    };
};
