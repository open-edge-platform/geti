// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import type { Media } from '@/api/types';
import { MediaItem } from '@/components/media-item/media-item.component';
import { MediaThumbnail } from '@/components/media-thumbnail/media-thumbnail.component';
import { useProjectIdentifier } from 'hooks/use-project-identifier.hook';

import { isOmeImage } from '../../../../shared/media-item-utils';
import { getThumbnailUrl } from '../../../../shared/media-url.utils';
import { getOmeDemoThumbnailUrl } from '../../../../shared/ome-demo';
import { AnnotationStatusIcon } from '../../gallery/annotation-state-icon.component';

type SidebarMediaItemProps = {
    item: Media;
    onSelectedMediaItem: (item: Media) => void;
};

export const SidebarMediaItem = ({ item, onSelectedMediaItem }: SidebarMediaItemProps) => {
    const projectId = useProjectIdentifier();

    return (
        <MediaItem
            contentElement={() => (
                <MediaThumbnail
                    item={item}
                    alt={item.name}
                    url={isOmeImage(item) ? getOmeDemoThumbnailUrl(item) : getThumbnailUrl(projectId, String(item.id))}
                    onClick={() => onSelectedMediaItem(item)}
                />
            )}
            bottomRightElement={() => {
                return <AnnotationStatusIcon isAnnotated={item.annotation_status.has_annotations} />;
            }}
        />
    );
};
