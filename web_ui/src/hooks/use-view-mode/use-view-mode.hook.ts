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

import { useLocalStorage } from 'usehooks-ts';

import { Subset } from '../../pages/project-details/components/project-model/training-dataset/utils';
import { MediaItemsBucketType } from '../../pages/project-details/components/project-test/media-items-bucket.interface';
import { MEDIA_CONTENT_BUCKET } from '../../providers/media-upload-provider/media-upload.interface';
import { INITIAL_VIEW_MODE } from '../../shared/components/media-view-modes/utils';
import { LOCAL_STORAGE_KEYS } from '../../shared/local-storage-keys';

type BucketType = MEDIA_CONTENT_BUCKET | Subset | MediaItemsBucketType;

const getMediaViewModeKey = (bucket: BucketType) => {
    return `${LOCAL_STORAGE_KEYS.MEDIA_VIEW_MODE}-${bucket.toString()}`;
};

export const useViewMode = (type: BucketType, defaultViewMode = INITIAL_VIEW_MODE) => {
    return useLocalStorage(getMediaViewModeKey(type), defaultViewMode);
};
