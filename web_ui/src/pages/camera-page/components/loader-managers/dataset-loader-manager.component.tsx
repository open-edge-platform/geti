// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useEffect } from 'react';

import intersectionWith from 'lodash/intersectionWith';

import { MediaUploadPerDataset } from '../../../../providers/media-upload-provider/media-upload.interface';
import { getIds, isNonEmptyArray } from '../../../../shared/utils';
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
