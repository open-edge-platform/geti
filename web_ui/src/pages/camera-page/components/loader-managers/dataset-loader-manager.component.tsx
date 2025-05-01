// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { getIds, isNonEmptyArray } from '@shared/utils';
import intersectionWith from 'lodash/intersectionWith';

import { MediaUploadPerDataset } from '../../../../providers/media-upload-provider/media-upload.interface';
import { Screenshot } from '../../../camera-support/camera.interface';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';

interface DatasetLoaderManagerProps {
    mediaUploadState: MediaUploadPerDataset;
}

const isEqualFileName = (a: Screenshot, b: { fileName: string }) => a.file.name === b.fileName;

export const DatasetLoaderManager = ({ mediaUploadState }: DatasetLoaderManagerProps) => {
    const { successList, errorList, isUploadInProgress } = mediaUploadState;

    const { savedFilesQuery, deleteMany } = useCameraStorage();
    const indexedDbFiles = savedFilesQuery.data ?? [];
    const acceptedFiles = indexedDbFiles.filter(({ isAccepted }) => isAccepted);

    useEffect(() => {
        const failedItems = isUploadInProgress ? [] : intersectionWith(acceptedFiles, errorList, isEqualFileName);
        const loadedItems = isUploadInProgress ? [] : intersectionWith(acceptedFiles, successList, isEqualFileName);

        if (isNonEmptyArray(loadedItems)) {
            deleteMany(getIds(loadedItems));
        }

        if (isNonEmptyArray(failedItems)) {
            deleteMany(getIds(failedItems));
        }
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [isUploadInProgress]);

    return <></>;
};
