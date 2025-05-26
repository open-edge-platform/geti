// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core';
import { Flex, Link as SpectrumLink, Text, View, VirtualizedHorizontalGrid } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import { Link } from 'react-router-dom';

import { isVideoFile } from '../../../../shared/media-utils';
import { getId } from '../../../../shared/utils';
import { Screenshot } from '../../../camera-support/camera.interface';
import { useCameraParams } from '../../hooks/camera-params.hook';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';
import { AnimatedThumbnail } from './animated-thumbnail';
import { ThumbnailPreview } from './thumbnail-preview.component';

interface SidebarThumbnailProps {
    screenshots: Screenshot[];
    isCloseSidebar?: boolean;
}

export const SidebarThumbnail = ({ screenshots, isCloseSidebar = false }: SidebarThumbnailProps): JSX.Element => {
    const { deleteMany } = useCameraStorage();
    const { isLivePrediction, defaultLabelId, hasDefaultLabel, ...identifier } = useCameraParams();

    const mediaGalleryPath = paths.project.dataset.capturedMediaGallery(identifier);

    if (isEmpty(screenshots)) {
        const height = isCloseSidebar ? 'size-800' : isLivePrediction ? 'size-3000' : 'size-2000';

        return (
            <Flex alignItems={'center'} justifyContent={'center'} height={height}>
                <Text>No media items available</Text>
            </Flex>
        );
    }

    if (isLivePrediction) {
        return <ThumbnailPreview screenshots={screenshots} isCloseSidebar={isCloseSidebar} />;
    }

    const handleDeleteItem = (id: string) => {
        return deleteMany([id]);
    };

    return (
        <>
            <VirtualizedHorizontalGrid
                items={screenshots}
                key={screenshots.map(getId).join('-')}
                containerHeight={isCloseSidebar ? `size-800` : `size-1250`}
                size={isCloseSidebar ? 60 : 96}
                idFormatter={getId}
                textValueFormatter={getId}
                renderItem={({ id, dataUrl, labelIds, file }) => (
                    <AnimatedThumbnail
                        id={id}
                        key={id}
                        url={String(dataUrl)}
                        labelIds={labelIds}
                        size={isCloseSidebar ? 'size-800' : 'size-1200'}
                        isVideo={isVideoFile(file)}
                        onDeleteItem={handleDeleteItem}
                    />
                )}
            />
            <View paddingTop={'size-250'} paddingBottom={isCloseSidebar ? '' : 'size-250'}>
                <SpectrumLink UNSAFE_style={{ color: 'var(--energy-blue)' }}>
                    <Link
                        to={hasDefaultLabel ? `${mediaGalleryPath}?defaultLabelId=${defaultLabelId}` : mediaGalleryPath}
                        viewTransition
                    >
                        View all captures
                    </Link>
                </SpectrumLink>
            </View>
        </>
    );
};
