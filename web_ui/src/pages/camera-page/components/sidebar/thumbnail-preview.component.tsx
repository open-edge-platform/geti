// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton } from '@geti/ui';
import { useOverlayTriggerState } from 'react-stately';

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
