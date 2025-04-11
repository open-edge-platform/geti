// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ChevronRight } from '../../../../assets/icons';
import { MediaItem } from '../../../../core/media/media.interface';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
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
