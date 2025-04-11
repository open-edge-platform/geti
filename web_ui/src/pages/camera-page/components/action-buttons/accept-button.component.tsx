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

import groupBy from 'lodash/groupBy';
import isEmpty from 'lodash/isEmpty';
import { useNavigate } from 'react-router-dom';

import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { paths } from '../../../../core/services/routes';
import { Button } from '../../../../shared/components/button/button.component';
import { getIds } from '../../../../shared/utils';
import { useDatasetMediaUpload } from '../../../project-details/components/project-dataset/hooks/dataset-media-upload';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';

interface AcceptButtonProps {
    isDisabled?: boolean;
    isPending?: boolean;
    onPress?: () => void;
}

const livePredictionPagePath = (datasetIdentifier: DatasetIdentifier) =>
    paths.project.tests.livePrediction(datasetIdentifier);

const datasetPagePath = (datasetIdentifier: DatasetIdentifier) => paths.project.dataset.index(datasetIdentifier);

export const AcceptButton = ({ isDisabled, isPending, onPress }: AcceptButtonProps): JSX.Element => {
    const navigate = useNavigate();
    const { isLivePrediction, ...datasetIdentifier } = useCameraParams();
    const { savedFilesQuery, updateMany } = useCameraStorage();
    const { mediaUploadState, onUploadMedia } = useDatasetMediaUpload();

    const savedFiles = savedFilesQuery.data ?? [];

    const handleRedirect = () => {
        isLivePrediction
            ? navigate(livePredictionPagePath(datasetIdentifier))
            : navigate(datasetPagePath(datasetIdentifier));
    };

    const handleStorageCheck = async () => {
        if (!mediaUploadState.insufficientStorage) {
            const updatedSavedFiles = await savedFilesQuery.refetch();
            const screenshotDict = groupBy(updatedSavedFiles.data, ({ labelIds }) => String(labelIds));
            await Promise.all(
                Object.entries(screenshotDict).map(async ([labelsIds, screenshots]) => {
                    await onUploadMedia({
                        labelIds: isEmpty(labelsIds) ? undefined : labelsIds.split(','),
                        files: screenshots.map(({ file }) => file),
                        datasetIdentifier,
                    });
                })
            );
        }
    };

    const handlePress = async () => {
        if (onPress) {
            onPress();
        }

        await updateMany(getIds(savedFiles), { isAccepted: true });

        handleStorageCheck();
        handleRedirect();
    };

    return (
        <Button variant={'accent'} isPending={isPending} isDisabled={isDisabled} onPress={handlePress}>
            Accept
        </Button>
    );
};
