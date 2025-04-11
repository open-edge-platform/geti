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

import { useOverlayTriggerState } from 'react-stately';

import { ActionButton } from '../../../../shared/components/button/button.component';
import { Screenshot } from '../../../camera-support/camera.interface';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';
import { ImageOverlay } from '../image-overlay.component';
import { AnimatedThumbnail } from './animated-thumbnail';

interface ThumbnailPreviewProps {
    screenshots: Screenshot[];
    defaultIndex?: number;
    isCloseSidebar?: boolean;
}

export const ThumbnailPreview = ({
    screenshots,
    defaultIndex = 0,
    isCloseSidebar = false,
}: ThumbnailPreviewProps): JSX.Element => {
    const { deleteMany } = useCameraStorage();
    const dialogState = useOverlayTriggerState({});

    const size = isCloseSidebar ? 'size-800' : 'size-3000';
    const currentImage = screenshots.at(defaultIndex) as Screenshot;

    const handleDeleteItem = (id: string) => {
        return deleteMany([id]);
    };

    return (
        <>
            <ActionButton width={size} height={size} aria-label={'open preview'} onPress={dialogState.toggle}>
                <AnimatedThumbnail
                    size={size}
                    isVideo={false}
                    id={currentImage.id}
                    url={String(currentImage.dataUrl)}
                    labelIds={currentImage.labelIds}
                    onDeleteItem={handleDeleteItem}
                    // button cannot appear as a descendant of button
                    hasDeleteButton={false}
                />
            </ActionButton>

            <ImageOverlay
                defaultIndex={0}
                dialogState={dialogState}
                screenshots={screenshots}
                onDeleteItem={() => handleDeleteItem(currentImage.id).then(dialogState.toggle)}
            />
        </>
    );
};
