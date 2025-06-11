// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import Webcam from 'react-webcam';
import { v4 as uuid } from 'uuid';

import { Label } from '../../../../core/labels/label.interface';
import { getIds } from '../../../../shared/utils';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';
import { CaptureButtonAnimation } from './capture-button-animation.component';

interface CapturePhotoButtonProps {
    webcamRef: React.RefObject<Webcam>;
    selectedLabels: Label[];
}

export const CapturePhotoButton = ({ webcamRef, selectedLabels }: CapturePhotoButtonProps) => {
    const { savedFilesQuery, saveMedia } = useCameraStorage();

    const saveItems = async () => {
        const dataUrl = webcamRef.current?.getScreenshot();
        const labelName = selectedLabels.at(-1)?.name ?? null;
        const id = uuid();

        saveMedia({ id, dataUrl, labelIds: getIds(selectedLabels), labelName });
    };

    return (
        <CaptureButtonAnimation videoTag={webcamRef.current?.video} onPress={saveItems}>
            {savedFilesQuery.data?.length || 0}
        </CaptureButtonAnimation>
    );
};
