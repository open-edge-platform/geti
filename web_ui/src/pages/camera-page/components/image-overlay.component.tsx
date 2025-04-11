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

import { MutableRefObject, useRef, useState } from 'react';

import { View } from '@adobe/react-spectrum';
import { Overlay } from '@react-spectrum/overlays';
import isNumber from 'lodash/isNumber';
import { useOverlay } from 'react-aria';
import { OverlayTriggerState, useOverlayTriggerState } from 'react-stately';

import { ChevronLeft, ChevronRight, Close } from '../../../assets/icons';
import { QuietActionButton } from '../../../shared/components/quiet-button/quiet-action-button.component';
import { isVideoFile } from '../../../shared/media-utils';
import { Screenshot } from '../../camera-support/camera.interface';
import { DeleteItemButton } from './delete-item-button.component';
import { ImageVideoFactory } from './image-video-factory.component';

import classes from './camera-page.module.scss';

interface ImageOverlayProps {
    screenshots: Screenshot[];
    defaultIndex: number;
    dialogState: OverlayTriggerState;
    onDeleteItem: (id: string) => void;
}

export const ImageOverlay = ({
    screenshots,
    dialogState,
    defaultIndex,
    onDeleteItem,
}: ImageOverlayProps): JSX.Element => {
    const container = useRef(null);
    const overlayRef = useRef(null);

    const alertDialogState = useOverlayTriggerState({});
    const [internalIndex, setInternalIndex] = useState<null | number>(null);
    const [imageAnimationClasses, setImageAnimationClasses] = useState([classes.thumbnailPreviewImage]);

    const currentIndex = isNumber(internalIndex) ? internalIndex : defaultIndex;
    const currentImage = screenshots.at(currentIndex);
    const showNavigationArrows = screenshots.length > 1;

    useOverlay(
        {
            isDismissable: true,
            shouldCloseOnBlur: false,
            isOpen: dialogState.isOpen,
            onClose: () => {
                setInternalIndex(null);
                dialogState.close();
            },
        },
        container
    );

    if (!currentImage) {
        return <></>;
    }

    return (
        <Overlay
            nodeRef={overlayRef as unknown as MutableRefObject<HTMLElement>}
            isOpen={dialogState.isOpen}
            onEntered={() => setImageAnimationClasses((prev) => [...prev, classes.thumbnailPreviewImageOpened])}
            onExiting={() =>
                setImageAnimationClasses((prev) => prev.filter((name) => name !== classes.thumbnailPreviewImageOpened))
            }
        >
            <View UNSAFE_className={classes.thumbnailPreviewContainer}>
                <div ref={container}>
                    <QuietActionButton
                        top={'size-400'}
                        left={'size-400'}
                        position={'absolute'}
                        onPress={() => {
                            dialogState.close();
                            alertDialogState.close();
                        }}
                        aria-label={'close preview'}
                        UNSAFE_className={classes.previewButton}
                    >
                        <Close width={20} height={20} />
                    </QuietActionButton>

                    <DeleteItemButton
                        top={'size-400'}
                        right={'size-400'}
                        position={'absolute'}
                        id={currentImage.id}
                        onDeleteItem={() => onDeleteItem(currentImage.id)}
                        alertDialogState={alertDialogState}
                        UNSAFE_className={classes.previewButton}
                    />

                    {showNavigationArrows && (
                        <QuietActionButton
                            top={'50%'}
                            left={'size-400'}
                            position={'absolute'}
                            UNSAFE_className={classes.previewButton}
                            onPress={() => {
                                const newIndex = currentIndex - 1;
                                setInternalIndex(newIndex < 0 ? screenshots.length - 1 : newIndex);
                            }}
                            aria-label={'previous item'}
                        >
                            <ChevronLeft width={20} height={20} />
                        </QuietActionButton>
                    )}

                    <ImageVideoFactory
                        alt={`user ${currentImage.id}`}
                        controls={true}
                        src={String(currentImage.dataUrl)}
                        isVideoFile={isVideoFile(currentImage.file)}
                        className={imageAnimationClasses.join(' ')}
                        aria-label={`full screen screenshot ${currentImage.id}`}
                    />

                    {showNavigationArrows && (
                        <QuietActionButton
                            top={'50%'}
                            right={'size-400'}
                            position={'absolute'}
                            UNSAFE_className={classes.previewButton}
                            onPress={() => {
                                const newIndex = currentIndex + 1;
                                setInternalIndex(newIndex >= screenshots.length ? 0 : newIndex);
                            }}
                            aria-label={'next item'}
                        >
                            <ChevronRight width={20} height={20} />
                        </QuietActionButton>
                    )}
                </div>
            </View>
        </Overlay>
    );
};
