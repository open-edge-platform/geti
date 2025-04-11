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

import { dimensionValue } from '@react-spectrum/utils';
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
            height={'size-900'}
            videoTag={webcamRef.current?.video}
            UNSAFE_style={{
                borderRadius: '50%',
                borderWidth: dimensionValue('size-50'),
            }}
            onPress={isLivePrediction ? saveLivePredictionItem : saveItems}
        >
            {isLivePrediction ? '' : savedFilesQuery.data?.length || 0}
        </CaptureButtonAnimation>
    );
};
