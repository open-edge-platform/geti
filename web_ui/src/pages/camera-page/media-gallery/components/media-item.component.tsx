// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useRef } from 'react';

import { DimensionValue, useUnwrapDOMRef, View } from '@geti/ui';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { Responsive } from '@react-types/shared';
import { isEmpty } from 'lodash-es';
import { usePress } from 'react-aria';

import { Label } from '../../../../core/labels/label.interface';
import { ViewModes } from '../../../../shared/components/media-view-modes/utils';
import { isVideoFile } from '../../../../shared/media-utils';
import { useTask } from '../../../annotator/providers/task-provider/task-provider.component';
import { ConsensedLabelSelector } from '../../components/condensed-label-selector.component';
import { DeleteItemButton } from '../../components/delete-item-button.component';
import { ImageVideoFactory } from '../../components/image-video-factory.component';
import { getSingleValidTask } from '../../util';
import { MediaItemContextMenu } from './media-item-context-menu.component';

import classes from './media-item.module.scss';

export interface MediaItemProps {
    id: string;
    url: string;
    labelIds: string[];
    mediaFile: File;
    viewMode?: ViewModes;
    height?: Responsive<DimensionValue>;
    onPress: (id: string) => void;
    onDeleteItem: (id: string) => void;
    onSelectLabel: (labels: Label[]) => void;
}

export const MediaItem = ({
    id,
    url,
    labelIds,
    mediaFile,
    viewMode,
    height,
    onPress,
    onDeleteItem,
    onSelectLabel,
}: MediaItemProps): JSX.Element => {
    const { tasks } = useTask();
    const containerRef = useRef(null);

    const alertDialogState = useOverlayTriggerState({});
    const labelSelectorState = useOverlayTriggerState({});
    const unwrappedContainerRef = useUnwrapDOMRef(containerRef);
    const { pressProps } = usePress({ onPress: () => onPress(id) });

    const filteredTasks = getSingleValidTask(tasks);
    const taskLabels = filteredTasks.flatMap(({ labels }) => labels);

    const contextMenuOptions: [string, () => void][] = isEmpty(taskLabels)
        ? [['Delete', alertDialogState.toggle]]
        : [
              ['Delete', alertDialogState.toggle],
              ['Edit Label', labelSelectorState.open],
          ];

    return (
        <View ref={containerRef} UNSAFE_className={classes.container} height={height}>
            <ImageVideoFactory
                src={url}
                isVideoFile={isVideoFile(mediaFile)}
                alt={`media item ${id}`}
                style={{ width: '100%', height: '100%', objectFit: 'cover', cursor: 'pointer' }}
                {...pressProps}
            />

            <DeleteItemButton
                id={id}
                top={'size-50'}
                right={'size-50'}
                position={'absolute'}
                onDeleteItem={onDeleteItem}
                alertDialogState={alertDialogState}
                UNSAFE_className={[classes.deleteContainer, alertDialogState.isOpen ? classes.visible : ''].join(' ')}
            />
            <ConsensedLabelSelector
                name={'Unlabeled'}
                labelIds={labelIds}
                right={'size-50'}
                bottom={'size-50'}
                viewMode={viewMode}
                position={'absolute'}
                isDisabled={isEmpty(taskLabels)}
                triggerState={labelSelectorState}
                selectedLabels={taskLabels.filter((label) => labelIds.includes(label.id))}
                onSelectLabel={onSelectLabel}
            />
            <MediaItemContextMenu containerRef={unwrappedContainerRef} options={contextMenuOptions} />
        </View>
    );
};
