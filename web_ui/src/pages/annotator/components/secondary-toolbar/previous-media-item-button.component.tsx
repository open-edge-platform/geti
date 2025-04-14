// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import minBy from 'lodash/minBy';

import { ChevronLeft } from '../../../../assets/icons';
import { Annotation } from '../../../../core/annotations/annotation.interface';
import { MediaItem } from '../../../../core/media/media.interface';
import { isVideo } from '../../../../core/media/video.interface';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { FindMediaItemCriteria, FindVideoFrameCriteria, useNextMediaItem } from '../../hooks/use-next-media-item.hook';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { findIndex } from '../../utils';
import { useConstructVideoFrame } from '../video-player/hooks/use-construct-video-frame.hook';

const findPreviousCriteria: FindMediaItemCriteria = (selectedMediaItem, mediaItems) => {
    const idx = findIndex(selectedMediaItem, mediaItems);

    if (idx > 0) {
        return { type: 'media', media: mediaItems[idx - 1] };
    }

    return undefined;
};

const findPreviousVideoFrameCriteria: FindVideoFrameCriteria = (selectedMediaItem, videoFrames) => {
    if (isVideo(selectedMediaItem)) {
        return { type: 'videoFrame', frameNumber: videoFrames[0] };
    }

    const selectedVideoFrameIndex = videoFrames.findIndex(
        (frameNumber) => frameNumber === selectedMediaItem.identifier.frameNumber
    );

    if (selectedVideoFrameIndex !== -1 && selectedVideoFrameIndex > 0) {
        const nextFrameNumber = videoFrames[selectedVideoFrameIndex - 1];
        return { type: 'videoFrame', frameNumber: nextFrameNumber };
    }

    // videoFrames is sorted
    const videoFrameIndexAfterSelectedFrame = videoFrames.findIndex(
        (frameNumber) => frameNumber > selectedMediaItem.identifier.frameNumber
    );

    if (videoFrameIndexAfterSelectedFrame === -1) {
        return undefined;
    }

    const nextFrameNumber = videoFrames[videoFrameIndexAfterSelectedFrame - 1];
    return { type: 'videoFrame', frameNumber: nextFrameNumber };
};

const findPreviousAnnotationCriteria = (selectedInput: Annotation | undefined, inputs: Annotation[]) => {
    const inputsBeforeSelectedInput = inputs.filter(({ id, zIndex }) => {
        if (selectedInput === undefined) {
            return true;
        }

        return id !== selectedInput.id && selectedInput.zIndex < zIndex;
    });

    return minBy(inputsBeforeSelectedInput, ({ zIndex }) => zIndex);
};

interface PreviousMediaItemButtonProps {
    selectMediaItem: (mediaItem: MediaItem) => void;
    selectedMediaItem: MediaItem | undefined;
}
export const PreviousMediaItemButton = ({
    selectMediaItem,
    selectedMediaItem,
}: PreviousMediaItemButtonProps): JSX.Element => {
    const annotationToolContext = useAnnotationToolContext();
    const nextMediaItem = useNextMediaItem(
        selectedMediaItem,
        findPreviousCriteria,
        findPreviousVideoFrameCriteria,
        findPreviousAnnotationCriteria
    );
    const constructVideoFrame = useConstructVideoFrame(selectedMediaItem);
    const isSceneBusy = useIsSceneBusy();

    const isDisabled = nextMediaItem === undefined || isSceneBusy;

    const goToPreviousMediaItem = () => {
        if (nextMediaItem === undefined) {
            return;
        }

        if (nextMediaItem.type === 'annotation') {
            annotationToolContext.scene.selectAnnotation(nextMediaItem.annotation.id);
            return;
        }

        if (nextMediaItem.type === 'videoFrame') {
            const videoFrame = constructVideoFrame(nextMediaItem.frameNumber);

            if (videoFrame !== undefined) {
                selectMediaItem(videoFrame);
            }
        }

        if (nextMediaItem.type !== 'media') {
            return;
        }

        selectMediaItem(nextMediaItem.media);
    };

    return (
        <QuietActionButton
            marginStart='size-125'
            id='secondary-toolbar-prev'
            aria-label='Previous media item'
            onPress={goToPreviousMediaItem}
            isDisabled={isDisabled}
        >
            <ChevronLeft />
        </QuietActionButton>
    );
};
