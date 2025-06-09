// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import Webcam from 'react-webcam';
import { v4 as uuid } from 'uuid';

import { Label } from '../../../../core/labels/label.interface';
import { getIds } from '../../../../shared/utils';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';
import { CaptureButtonAnimation } from './capture-button-animation.component';

interface CapturePhotoButtonProps {
    webcamRef: React.RefObject<Webcam>;
    selectedLabels: Label[];
}

export const CapturePhotoButton = ({ webcamRef, selectedLabels }: CapturePhotoButtonProps) => {
    const { isLivePrediction } = useCameraParams();
    const { savedFilesQuery, deleteAllItems, saveMedia } = useCameraStorage();

    const saveItems = async () => {
        const dataUrl = webcamRef.current?.getScreenshot();
        const labelName = selectedLabels.at(-1)?.name ?? null;
        const id = uuid();

        saveMedia({ id, dataUrl, labelIds: getIds(selectedLabels), labelName });
    };

    const saveLivePredictionItem = () => deleteAllItems(false).then(saveItems);

    return (
        <CaptureButtonAnimation
            videoTag={webcamRef.current?.video}
            onPress={isLivePrediction ? saveLivePredictionItem : saveItems}
        >
            {isLivePrediction ? '' : savedFilesQuery.data?.length || 0}
        </CaptureButtonAnimation>
    );
};
