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

import { MEDIA_TYPE } from './base-media.interface';
import { BaseIdentifier, BaseMediaItem } from './base.interface';

export interface ImageIdentifier extends BaseIdentifier {
    type: MEDIA_TYPE.IMAGE;
    imageId: string;
}

export interface Image extends BaseMediaItem {
    identifier: ImageIdentifier;
}

export const isImage = (media: { identifier: BaseIdentifier } | undefined): media is Image => {
    return media !== undefined && media.identifier.type === MEDIA_TYPE.IMAGE;
};
