// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
