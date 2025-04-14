// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { MediaItem } from '../../../../../core/media/media.interface';
import { TestMediaItem } from '../../../../../core/tests/test-media.interface';
import { isSelected } from '../../../../../pages/annotator/components/sidebar/dataset/utils';

export const getSelectedItemIndex = (
    selectedItem: TestMediaItem | MediaItem,
    mediaItemsList: (TestMediaItem | MediaItem)[],
    showFramesSeparately?: boolean
): number =>
    mediaItemsList.findIndex((currentItem) =>
        isSelected(
            'media' in currentItem ? currentItem.media : currentItem,
            'media' in selectedItem ? selectedItem.media : selectedItem,
            showFramesSeparately
        )
    );
