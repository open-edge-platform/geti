// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@geti/ui';
import { FooterProps, Footer as FooterView, View } from '@react-spectrum/view';
import clsx from 'clsx';

import { MediaItem } from '../../../../core/media/media.interface';
import { isVideo, isVideoFrame } from '../../../../core/media/video.interface';
import { useProject } from '../../../project-details/providers/project-provider/project-provider.component';
import { useZoom } from '../../zoom/zoom-provider.component';
import { FitImageToScreenButton } from '../fit-image-to-screen-button/fit-image-to-screen-button.component';
import { MediaItemImageMetadata } from './media-item-image-metadata.component';
import { MediaItemVideoMetadata } from './media-item-video-metadata.component';
import { ProjectName } from './project-name.component';
import { ZoomLevel } from './zoom-level/zoom-level.component';

import classes from './annotator-footer.module.scss';

interface CustomFooterProps extends Omit<FooterProps, 'children'> {
    selectedItem: MediaItem | undefined;
    areActionsDisabled?: boolean;
    children?: JSX.Element;
}

export const Footer = ({
    selectedItem,
    areActionsDisabled = false,
    children,
    ...footerProps
}: CustomFooterProps): JSX.Element => {
    const {
        zoomState: { zoom },
    } = useZoom();

    const { project, isTaskChainProject } = useProject();

    const isVideoOrVideoFrame = selectedItem && (isVideo(selectedItem) || isVideoFrame(selectedItem));

    return (
        <FooterView {...footerProps} data-testid={'footer'}>
            <View backgroundColor='gray-100' height='100%' aria-label='footer'>
                <Flex justifyContent='space-between' height='100%'>
                    {children}
                    <Flex height='100%' alignItems='center'>
                        <Flex alignItems='center' justifyContent='end'>
                            {isTaskChainProject ? <ProjectName name={project.name} /> : <></>}

                            {selectedItem !== undefined && (
                                <>
                                    {isVideoOrVideoFrame ? (
                                        <MediaItemVideoMetadata mediaItem={selectedItem} />
                                    ) : (
                                        <MediaItemImageMetadata mediaItem={selectedItem} />
                                    )}
                                </>
                            )}
                            {!areActionsDisabled && <FitImageToScreenButton />}
                            <Flex
                                alignItems={'center'}
                                UNSAFE_className={clsx(classes.zoomLevel, {
                                    [classes.metaItemLeftBorder]: !areActionsDisabled,
                                })}
                            >
                                <ZoomLevel zoom={zoom} />
                            </Flex>
                        </Flex>
                    </Flex>
                </Flex>
            </View>
        </FooterView>
    );
};
