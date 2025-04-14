// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
