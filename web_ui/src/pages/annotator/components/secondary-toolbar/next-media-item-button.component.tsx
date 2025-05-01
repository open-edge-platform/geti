// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { QuietActionButton } from '@shared/components/quiet-button/quiet-action-button.component';

import { ChevronRight } from '../../../../assets/icons';
import { MediaItem } from '../../../../core/media/media.interface';
import { useIsSceneBusy } from '../../hooks/use-annotator-scene-interaction-state.hook';
import { useNextMediaItem } from '../../hooks/use-next-media-item.hook';
import { useAnnotationToolContext } from '../../providers/annotation-tool-provider/annotation-tool-provider.component';
import { findNextAnnotationCriteria, findNextCriteria, findNextVideoFrameCriteria } from '../utils';
import { useConstructVideoFrame } from '../video-player/hooks/use-construct-video-frame.hook';

interface NextMediaItemButtonProps {
    selectMediaItem: (mediaItem: MediaItem) => void;
    selectedMediaItem: MediaItem | undefined;
}
export const NextMediaItemButton = ({ selectMediaItem, selectedMediaItem }: NextMediaItemButtonProps): JSX.Element => {
    // Use context to select annotation
    const annotationToolContext = useAnnotationToolContext();
    const nextMediaItem = useNextMediaItem(
        selectedMediaItem,
        findNextCriteria,
        findNextVideoFrameCriteria,
        findNextAnnotationCriteria
    );
    const constructVideoFrame = useConstructVideoFrame(selectedMediaItem);
    const isSceneBusy = useIsSceneBusy();

    const isDisabled = nextMediaItem === undefined || isSceneBusy;

    const selectNextActiveMediaItem = () => {
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
            id='secondary-toolbar-next'
            aria-label='Next media item'
            onPress={selectNextActiveMediaItem}
            isDisabled={isDisabled}
        >
            <ChevronRight />
        </QuietActionButton>
    );
};
