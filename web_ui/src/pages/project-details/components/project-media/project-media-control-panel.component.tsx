// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Dispatch, SetStateAction } from 'react';

import { Checkbox, dimensionValue, Flex, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { Delete } from '@geti/ui/icons';
import { isEmpty } from 'lodash-es';

import { isVideo } from '../../../../core/media/video.interface';
import { useSortingParams } from '../../../../hooks/use-sorting-params/use-sorting-params.hook';
import { MediaViewModes } from '../../../../shared/components/media-view-modes/media-view-modes.component';
import { ViewModes } from '../../../../shared/components/media-view-modes/utils';
import { MenuTriggerPopup } from '../../../../shared/components/menu-trigger-popup/menu-trigger-popup.component';
import { UploadMediaButton } from '../../../../shared/components/upload-media/upload-media-button/upload-media-button.component';
import { MediaSearch } from '../../../media/media-actions/media-search.component';
import { MediaSorting } from '../../../media/media-actions/media-sorting.component';
import { MediaFilter } from '../../../media/media-filter.component';
import { useMedia } from '../../../media/providers/media-provider.component';
import { ExportImportDatasetButtons } from '../project-dataset/export-dataset/export-import-dataset-buttons.component';
import { MediaCount } from './media-count.component';
import { DELETE_ANOMALY_VIDEO_WARNING } from './media-item-tooltip-message/utils';
import { DELETE_SELECTED_MEDIA_LABEL, SELECT_ALL_LABEL, UPLOAD_MEDIA_LABEL } from './utils';

interface ProjectMediaControlPanelProps {
    viewMode: ViewModes;
    countElements: string;
    isAnomalyProject: boolean;
    hasExportImportButtons: boolean;
    isInUploadingState: boolean;
    setViewMode: Dispatch<SetStateAction<ViewModes>>;
    uploadMediaCallback: (files: File[]) => void;
    onCameraSelected: () => void;
}

export const ProjectMediaControlPanel = ({
    viewMode,
    countElements,
    isAnomalyProject,
    isInUploadingState,
    hasExportImportButtons,
    setViewMode,
    onCameraSelected,
    uploadMediaCallback,
}: ProjectMediaControlPanelProps): JSX.Element => {
    const { sortingOptions, setSortingOptions } = useSortingParams();

    const {
        media,
        mediaSelection,
        mediaFilterOptions,
        deleteMedia,
        isMediaFetching,
        isMediaFilterEmpty,
        totalMatchedImages,
        totalMatchedVideos,
        resetMediaSelection,
        setMediaFilterOptions,
        addBulkMediaToSelection,
    } = useMedia();

    const hasMediaItems = !isEmpty(media);
    const selectedItems = mediaSelection.length;
    const hasAnomalyVideo = isAnomalyProject && mediaSelection.some(isVideo);
    const areAllSelected = !isEmpty(mediaSelection) && selectedItems === media.length;
    const isIndeterminate = !isEmpty(mediaSelection) && selectedItems < media.length;
    const additionalDeletionInformation = hasAnomalyVideo ? DELETE_ANOMALY_VIDEO_WARNING : '';
    const areControlsDisabled = !(hasMediaItems || !isMediaFilterEmpty);
    const showSelectionActions = !areControlsDisabled && !isEmpty(mediaSelection);

    const totalMatches = totalMatchedImages + totalMatchedVideos;
    const deletionConfirmation = `Are you sure you want to delete ${mediaSelection.length} of ${media.length} items?`;

    const onDeleteMedia = () =>
        deleteMedia.mutate(mediaSelection, {
            onSuccess: () => resetMediaSelection(),
        });

    return (
        <View>
            <Flex gap='size-100' alignItems='center' justifyContent='space-between'>
                <Flex gap='size-100' alignItems={'center'} flex={1} isHidden={areControlsDisabled}>
                    <TooltipTrigger placement={'bottom'}>
                        <Checkbox
                            aria-label={SELECT_ALL_LABEL}
                            isSelected={areAllSelected}
                            isIndeterminate={isIndeterminate}
                            isDisabled={!hasMediaItems || isInUploadingState}
                            marginStart={'size-75'}
                            onChange={(state: boolean) =>
                                state ? addBulkMediaToSelection(media) : resetMediaSelection()
                            }
                        />
                        <Tooltip>{SELECT_ALL_LABEL}</Tooltip>
                    </TooltipTrigger>

                    {showSelectionActions && (
                        <Flex alignItems='center' UNSAFE_style={{ padding: dimensionValue('size-50') }}>
                            <MenuTriggerPopup
                                onPrimaryAction={onDeleteMedia}
                                ariaLabel={DELETE_SELECTED_MEDIA_LABEL}
                                isButtonDisabled={deleteMedia.isPending}
                                question={`${deletionConfirmation} ${additionalDeletionInformation}`}
                            >
                                <Delete data-testid='delete-media-id' id='delete-media-id' />
                            </MenuTriggerPopup>
                        </Flex>
                    )}
                    {!isAnomalyProject && <MediaCount countMessage={countElements} selectedItems={selectedItems} />}
                </Flex>

                {!showSelectionActions && !areControlsDisabled && (
                    <Flex alignItems='center' UNSAFE_style={{ padding: dimensionValue('size-50') }}>
                        <MediaSearch
                            mediaFilterOptions={mediaFilterOptions}
                            setMediaFilterOptions={setMediaFilterOptions}
                            isDisabled={isInUploadingState}
                        />

                        <MediaFilter
                            filterOptions={mediaFilterOptions}
                            onSetFilterOptions={setMediaFilterOptions}
                            totalMatches={totalMatches}
                            isMediaFetching={isMediaFetching}
                            isMediaFilterEmpty={isMediaFilterEmpty}
                            isDisabled={isInUploadingState}
                        />

                        <MediaViewModes viewMode={viewMode} isDisabled={isInUploadingState} setViewMode={setViewMode} />

                        <MediaSorting
                            isDisabled={isInUploadingState}
                            sortingOptions={sortingOptions}
                            setSortingOptions={setSortingOptions}
                        />

                        <Flex alignItems={'center'} marginStart={'size-100'} gap={'size-100'}>
                            {hasExportImportButtons && <ExportImportDatasetButtons hasMediaItems={hasMediaItems} />}

                            <UploadMediaButton
                                title={UPLOAD_MEDIA_LABEL}
                                id={'upload-media-action-menu'}
                                uploadCallback={uploadMediaCallback}
                                onCameraSelected={onCameraSelected}
                            />
                        </Flex>
                    </Flex>
                )}
            </Flex>
        </View>
    );
};
