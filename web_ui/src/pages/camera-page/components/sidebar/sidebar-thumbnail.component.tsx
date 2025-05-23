// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { paths } from '@geti/core/src/services/routes';
import { dimensionValue, Flex, Link as SpectrumLink, Text, View } from '@geti/ui';
import { isEmpty } from 'lodash-es';
import useVirtual from 'react-cool-virtual';
import { Link } from 'react-router-dom';

import { isVideoFile } from '../../../../shared/media-utils';
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

    const { outerRef, innerRef, items } = useVirtual<HTMLDivElement, HTMLDivElement>({
        horizontal: true,
        itemCount: screenshots.length,
        // itemSize doesn't accept strings so we had to hardcode the width values, but for
        // reference I added them here:
        // --spectrum-global-dimension-size-800: 64px;
        //--spectrum-global-dimension-size-1200: 96px;
        //
        // https://github.com/adobe/react-spectrum/blob/main/packages/@adobe/spectrum-css-temp/vars/spectrum-medium.css
        itemSize: () => (isCloseSidebar ? 64 : 96),
        overscanCount: 6,
    });

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

    // Prevent discard-all/new photo TypeError error
    const isVirtualListUpToDate = screenshots.length >= items.length;

    const handleDeleteItem = (id: string) => {
        return deleteMany([id]);
    };

    return (
        <>
            <div
                ref={outerRef}
                style={{
                    height: isCloseSidebar ? dimensionValue('size-800') : 'auto',
                    overflow: 'auto hidden',
                    paddingBottom: dimensionValue('size-100'),
                }}
            >
                <div
                    ref={innerRef}
                    style={{
                        display: 'flex',
                        gap: isCloseSidebar ? dimensionValue('size-100') : dimensionValue('size-200'),
                    }}
                >
                    {isVirtualListUpToDate &&
                        items.map(({ index }) => {
                            const { id, dataUrl, labelIds, file } = screenshots[index];

                            return (
                                <AnimatedThumbnail
                                    id={id}
                                    key={id}
                                    url={String(dataUrl)}
                                    labelIds={labelIds}
                                    size={isCloseSidebar ? 'size-800' : 'size-1200'}
                                    isVideo={isVideoFile(file)}
                                    onDeleteItem={handleDeleteItem}
                                />
                            );
                        })}
                </div>
            </div>
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
