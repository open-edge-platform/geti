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

import { useState } from 'react';

import { AlertDialog, ButtonGroup, DialogTrigger } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import { NavigateFunction, useNavigate } from 'react-router-dom';
import { useIsMounted } from 'usehooks-ts';

import { DatasetIdentifier } from '../../../../core/projects/dataset.interface';
import { paths } from '../../../../core/services/routes';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { Button } from '../../../../shared/components/button/button.component';
import { runWhen } from '../../../../shared/utils';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';
import { AcceptButton } from './accept-button.component';
import { TakeShotsButton } from './take-shots-button.component';

interface ActionButtonsProps {
    isDisabled?: boolean;
    canGoToCameraPage?: boolean;
}

interface ButtonCancelAction {
    deleteAllItems: () => Promise<void>;
    navigate: NavigateFunction;
    datasetIdentifier: DatasetIdentifier;
}

const livePredictionPagePath = (datasetIdentifier: DatasetIdentifier) =>
    paths.project.tests.livePrediction(datasetIdentifier);

const datasetPagePath = (datasetIdentifier: DatasetIdentifier) => paths.project.dataset.index(datasetIdentifier);

const CancelButton = ({
    isLivePrediction,
    datasetIdentifier,
    navigate,
    deleteAllItems,
}: ButtonCancelAction & { isLivePrediction: boolean }) => {
    return (
        <Button
            variant={'primary'}
            marginEnd={'size-65'}
            onPress={async () => {
                if (isLivePrediction) {
                    await deleteAllItems();
                    navigate(livePredictionPagePath(datasetIdentifier));
                } else {
                    navigate(datasetPagePath(datasetIdentifier));
                }
            }}
        >
            Cancel
        </Button>
    );
};

const DiscardAllButton = ({
    isDisabled,
    datasetIdentifier,
    navigate,
    deleteAllItems,
}: ButtonCancelAction & { isDisabled: boolean }) => {
    const isMounted = useIsMounted();
    const [isDiscarding, setIsDiscarding] = useState(false);

    const onComponentIsMounted = runWhen<MediaDeviceInfo[]>(isMounted);

    return (
        <DialogTrigger>
            <Button marginEnd={'size-65'} variant={'primary'} isDisabled={isDisabled}>
                Discard all
            </Button>

            <AlertDialog
                title={'Discard all'}
                cancelLabel={'Cancel'}
                variant={'destructive'}
                isPrimaryActionDisabled={isDiscarding}
                primaryActionLabel={isDiscarding ? 'Discarding...' : 'Discard all'}
                onPrimaryAction={async () => {
                    setIsDiscarding(true);

                    await deleteAllItems();

                    onComponentIsMounted(() => {
                        setIsDiscarding(false);
                        navigate(datasetPagePath(datasetIdentifier));
                    });
                }}
            >
                {/* TODO: Change to "discard all images and videos" once we support videos" */}
                Are you sure you want to discard all images?
            </AlertDialog>
        </DialogTrigger>
    );
};

export const ActionButtons = ({ isDisabled, canGoToCameraPage }: ActionButtonsProps): JSX.Element => {
    const navigate = useNavigate();
    const { isLivePrediction, ...datasetIdentifier } = useCameraParams();
    const { deleteAllItems, savedFilesQuery } = useCameraStorage();
    const { addNotification } = useNotification();
    const [isPending, setIsPending] = useState(false);

    const isEmptyItems = isEmpty(savedFilesQuery.data);
    const ButtonComponent = isLivePrediction || isEmptyItems ? CancelButton : DiscardAllButton;

    const handleOnPress = () => {
        setIsPending(true);
        addNotification({ message: 'Preparing media upload...', type: NOTIFICATION_TYPE.INFO });
    };

    return (
        <ButtonGroup>
            <ButtonComponent
                navigate={navigate}
                deleteAllItems={deleteAllItems}
                isLivePrediction={isLivePrediction}
                datasetIdentifier={datasetIdentifier}
                isDisabled={isDisabled || isEmptyItems}
            />

            {canGoToCameraPage && <TakeShotsButton />}

            <AcceptButton isDisabled={isDisabled || isEmptyItems} onPress={handleOnPress} isPending={isPending} />
        </ButtonGroup>
    );
};
