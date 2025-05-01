// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef, useState } from 'react';

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { View } from '@react-spectrum/view';
import { Checkbox } from '@shared/components/checkbox/checkbox.component';
import { MediaItemView } from '@shared/components/media-item-view/media-item-view.component';
import { PressableElement } from '@shared/components/pressable-element/pressable-element.component';

import { MediaItem } from '../../../../core/media/media.interface';
import { MediaItemActions } from './media-item-actions/media-item-actions.component';
import { MediaItemTooltipMessage } from './media-item-tooltip-message/media-item-tooltip-message';
import { getMediaItemTooltipProps } from './media-item-tooltip-message/utils';

import classes from './grid-media-item.module.scss';

interface GridMediaItemProps {
    id: string;
    mediaItem: MediaItem;
    isSelected: boolean;
    isLargeSize: boolean;
    isAtLeastOneMediaItemSelected?: boolean;
    handleDblClick: () => void;
    toggleMediaSelection: () => void;
    shouldShowAnnotationIndicator: boolean;
}

export const GridMediaItem = ({
    id,
    mediaItem,
    isSelected,
    isAtLeastOneMediaItemSelected,
    isLargeSize,
    handleDblClick,
    toggleMediaSelection,
    shouldShowAnnotationIndicator,
}: GridMediaItemProps): JSX.Element => {
    const triggerRef = useRef(null);

    const [isHovered, setIsHovered] = useState(false);

    const handlePointerOver = () => {
        setIsHovered(true);
    };

    const handlePointerOut = () => {
        setIsHovered(false);
    };

    const tooltipProps = getMediaItemTooltipProps(mediaItem);
    const pressProps = isLargeSize
        ? { onDoubleClick: handleDblClick, onClick: isAtLeastOneMediaItemSelected ? toggleMediaSelection : undefined }
        : { onClick: handleDblClick };

    return (
        <div
            id={`grid-media-item-${id}`}
            className={[classes.mediaItem, isSelected ? classes.mediaItemSelected : ''].join(' ')}
            onPointerOver={handlePointerOver}
            onPointerOut={handlePointerOut}
        >
            {(isHovered || isSelected) && (
                <Flex
                    wrap
                    ref={triggerRef}
                    width={'100%'}
                    position={'absolute'}
                    justifyContent={'space-between'}
                    UNSAFE_className={classes.mediaItemActionsWrapper}
                >
                    <View width='size-500' height='size-500' zIndex={4}>
                        <Flex
                            position='relative'
                            justifyContent='center'
                            alignItems='center'
                            width='100%'
                            height='100%'
                        >
                            <View
                                width={'100%'}
                                height={'100%'}
                                position={'absolute'}
                                borderRadius={'regular'}
                                backgroundColor={'gray-50'}
                            />
                            <Checkbox
                                aria-label={'Select media item'}
                                isSelected={isSelected}
                                onChange={toggleMediaSelection}
                                UNSAFE_style={{ padding: 8 }}
                            />
                        </Flex>
                    </View>

                    <View
                        backgroundColor={'gray-50'}
                        borderRadius={'regular'}
                        UNSAFE_style={{ boxSizing: 'border-box', display: 'flex', alignItems: 'center' }}
                        paddingY={'size-150'}
                        paddingX={'size-75'}
                        height={'size-500'}
                        zIndex={10}
                    >
                        <MediaItemActions mediaItem={mediaItem} />
                    </View>
                </Flex>
            )}

            <TooltipTrigger>
                <PressableElement {...pressProps}>
                    <MediaItemView
                        mediaItem={mediaItem}
                        shouldShowAnnotationIndicator={shouldShowAnnotationIndicator}
                    />
                </PressableElement>
                <Tooltip>
                    <MediaItemTooltipMessage {...tooltipProps} />
                </Tooltip>
            </TooltipTrigger>
        </div>
    );
};
