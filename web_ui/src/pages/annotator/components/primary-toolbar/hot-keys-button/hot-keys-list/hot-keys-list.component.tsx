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

import { Divider, Text, View } from '@adobe/react-spectrum';

import { isVideo, isVideoFrame } from '../../../../../../core/media/video.interface';
import { getKeyName } from '../../../../../../shared/hotkeys';
import { ToolType } from '../../../../core/annotation-tool-context.interface';
import { useAnnotatorHotkeys } from '../../../../hooks/use-hotkeys-configuration.hook';
import { useSelectedMediaItem } from '../../../../providers/selected-media-item-provider/selected-media-item-provider.component';
import { useTask } from '../../../../providers/task-provider/task-provider.component';
import { toolTypeToLabelMapping } from '../../../../tools/utils';
import { HotKeysItem } from '../hot-keys-item/hot-keys-item.component';
import { useAvailabilityOfHotkeys } from '../use-availability-of-hotkeys.hook';

import classes from './hot-keys-list.module.scss';

export const HotKeysList = (): JSX.Element => {
    const { hotkeys } = useAnnotatorHotkeys();
    const { activeDomains } = useTask();
    const { selectedMediaItem } = useSelectedMediaItem();

    const hotkeysAvailability = useAvailabilityOfHotkeys(activeDomains);

    const isVideoLoaded = selectedMediaItem && (isVideo(selectedMediaItem) || isVideoFrame(selectedMediaItem));

    const redoShortcut = (
        <>
            {getKeyName(hotkeys.redo)}
            <Text UNSAFE_className={classes.hotKeysListRedo}> or </Text>
            {getKeyName(hotkeys.redoSecond)}
        </>
    );

    const imageDragShortcut = (
        <>
            {getKeyName(hotkeys.imageDrag)}
            <Text UNSAFE_className={classes.hotKeysListRedo}> or </Text>
            {getKeyName(hotkeys.imageDragSecond)}
        </>
    );

    const deleteShortcut = (
        <>
            {getKeyName(hotkeys.delete)}
            <Text UNSAFE_className={classes.hotKeysListRedo}> or </Text>
            {getKeyName(hotkeys.deleteSecond)}
        </>
    );

    return (
        <View marginTop={'size-150'} height={'100%'} UNSAFE_className={classes.hotKeysListContainer}>
            <HotKeysItem title={'Save annotation(s)'} shortcut={hotkeys.saveAnnotations} />
            <Divider size={'S'} marginBottom={'size-150'} />
            <HotKeysItem title={'Select all'} shortcut={hotkeys.selectAll} />
            <HotKeysItem title={'Deselect all'} shortcut={hotkeys.deselectAll} />
            <HotKeysItem title={'Show or hide all'} shortcut={hotkeys.hideAllAnnotations} />
            <Divider size={'S'} marginBottom={'size-150'} />
            <HotKeysItem title={'Undo'} shortcut={hotkeys.undo} />
            <HotKeysItem title={'Redo'} shortcut={redoShortcut} />
            <Divider size={'S'} marginBottom={'size-150'} />
            <HotKeysItem title={'Deleting selected'} shortcut={deleteShortcut} />
            <HotKeysItem title={'Copy selected'} shortcut={hotkeys.copyAnnotation} />
            <HotKeysItem title={'Paste selected'} shortcut={hotkeys.pasteAnnotation} />
            <Divider size={'S'} marginBottom={'size-150'} />
            <HotKeysItem title={toolTypeToLabelMapping[ToolType.SelectTool]} shortcut={hotkeys['select-tool']} />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.BoxTool]}
                shortcut={hotkeys['bounding-box-tool']}
                disabled={!hotkeysAvailability['bounding-box-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.RotatedBoxTool]}
                shortcut={hotkeys['rotated-bounding-box-tool']}
                disabled={!hotkeysAvailability['rotated-bounding-box-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.SSIMTool]}
                shortcut={hotkeys['ssim-tool']}
                disabled={!hotkeysAvailability['ssim-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.CircleTool]}
                shortcut={hotkeys['circle-tool']}
                disabled={!hotkeysAvailability['circle-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.PolygonTool]}
                shortcut={hotkeys['polygon-tool']}
                disabled={!hotkeysAvailability['polygon-tool']}
            />
            <HotKeysItem
                title={`${toolTypeToLabelMapping[ToolType.PolygonTool]} - snapping mode`}
                shortcut={hotkeys['magneticLasso']}
                disabled={!hotkeysAvailability['polygon-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.GrabcutTool]}
                shortcut={hotkeys['grabcut-tool']}
                disabled={!hotkeysAvailability['grabcut-tool']}
            />
            <HotKeysItem
                title={`${toolTypeToLabelMapping[ToolType.GrabcutTool]} - add to selection`}
                shortcut={hotkeys['grabcut-foreground-tool']}
                disabled={!hotkeysAvailability['grabcut-tool']}
            />
            <HotKeysItem
                title={`${toolTypeToLabelMapping[ToolType.GrabcutTool]} - subtract from selection`}
                shortcut={hotkeys['grabcut-background-tool']}
                disabled={!hotkeysAvailability['grabcut-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.WatershedTool]}
                shortcut={hotkeys['watershed-tool']}
                disabled={!hotkeysAvailability['watershed-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.RITMTool]}
                shortcut={hotkeys['ritm-tool']}
                disabled={!hotkeysAvailability['ritm-tool']}
            />
            <HotKeysItem
                title={toolTypeToLabelMapping[ToolType.Explanation]}
                shortcut={hotkeys['explanation']}
                disabled={!hotkeysAvailability['explanation']}
            />
            <HotKeysItem title={'Fit image to screen'} shortcut={hotkeys.zoom} />
            <HotKeysItem title={'Scroll image with hand tool'} shortcut={imageDragShortcut} />
            <Divider size={'S'} marginBottom={'size-150'} />
            <HotKeysItem title={'Play / Pause video'} shortcut={hotkeys.playOrPause} disabled={!isVideoLoaded} />
            <HotKeysItem title={'Next frame'} shortcut={hotkeys.nextFrame} disabled={!isVideoLoaded} />
            <HotKeysItem title={'Previous frame'} shortcut={hotkeys.previousFrame} disabled={!isVideoLoaded} />
        </View>
    );
};
