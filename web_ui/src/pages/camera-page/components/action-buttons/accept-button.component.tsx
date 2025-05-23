// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { Button } from '@geti/ui';
import { groupBy, isEmpty } from 'lodash-es';
import { useNavigate } from 'react-router-dom';

import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
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

        await handleStorageCheck();
        handleRedirect();
    };

    return (
        <Button variant={'accent'} isPending={isPending} isDisabled={isDisabled} onPress={handlePress}>
            Accept
        </Button>
    );
};
