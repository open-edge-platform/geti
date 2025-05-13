// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useState } from 'react';

import { isEmpty, isNil, noop } from 'lodash-es';
import { useOverlayTriggerState } from 'react-stately';

import { MediaItemsList as MediaListVirtuoso } from '../../../../shared/components/media-items-list/media-items-list.component';
import { ViewModes } from '../../../../shared/components/media-view-modes/utils';
import { getIds } from '../../../../shared/utils';
import { Screenshot } from '../../../camera-support/camera.interface';
import { ImageOverlay } from '../../components/image-overlay.component';
import { useCameraStorage } from '../../hooks/use-camera-storage.hook';
import { MediaItem } from './media-item.component';

interface MediaItemsListProps {
    viewMode: ViewModes;
    screenshots: Screenshot[];
}

export const MediaItemsList = ({ viewMode, screenshots }: MediaItemsListProps): JSX.Element => {
    const dialogState = useOverlayTriggerState({});
    const [previewIndex, setPreviewIndex] = useState<null | number>(0);
    const { deleteMany, updateMany } = useCameraStorage();

    const handleDeleteItem = (id: string) => {
        return deleteMany([id]);
    };

    return (
        <>
            <MediaListVirtuoso
                endReached={noop}
                viewMode={viewMode}
                marginTop={'size-115'}
                totalCount={screenshots.length}
                height={`calc(100% - size-550)`}
                itemContent={(index) => {
                    const { id, ...itemData } = screenshots[index];

                    return (
                        <MediaItem
                            id={id}
                            key={id}
                            onPress={() => {
                                setPreviewIndex(index);
                                dialogState.open();
                            }}
                            viewMode={viewMode}
                            mediaFile={itemData.file}
                            url={String(itemData.dataUrl)}
                            labelIds={itemData.labelIds}
                            onDeleteItem={handleDeleteItem}
                            onSelectLabel={(newLabels) => {
                                if (isEmpty(newLabels)) {
                                    updateMany([id], { ...itemData, labelIds: [], labelName: null });
                                } else {
                                    const newLabelIds = getIds(newLabels);
                                    const newLabelName = newLabels.at(-1)?.name || null;

                                    updateMany([id], { ...itemData, labelIds: newLabelIds, labelName: newLabelName });
                                }
                            }}
                        />
                    );
                }}
            />
            {!isNil(previewIndex) && (
                <ImageOverlay
                    dialogState={dialogState}
                    screenshots={screenshots}
                    defaultIndex={previewIndex}
                    onDeleteItem={(id) => {
                        handleDeleteItem(id).then(() => {
                            dialogState.close();
                            setPreviewIndex(null);
                        });
                    }}
                />
            )}
        </>
    );
};
