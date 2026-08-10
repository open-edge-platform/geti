// Copyright (C) 2025 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Dispatch, SetStateAction, useMemo } from 'react';

import type { Media } from '@/api/types';
import {
    ActionButton,
    Button,
    ButtonGroup,
    Checkbox,
    dimensionValue,
    Divider,
    Flex,
    MediaViewModes,
    ViewModes,
} from '@geti-ui/ui';
import { SortDown, SortUp } from '@geti-ui/ui/icons';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { isString } from 'lodash-es';

import { isImage } from '../../../../shared/media-item-utils';
import { TrainModel } from '../../../models/train-model/train-model.component';
import { ImportExport } from '../../import-export/import-export.component';
import { useSelectedData } from '../../providers/selected-data-provider.component';
import { DeleteMediaItem } from '../delete-media-item/delete-media-item.component';
import { useSelectDatasetItem } from '../hooks/use-select-dataset-item.hook';
import { AssignLabel } from './assign-label.component';
import { DatasetStatistics } from './dataset-statistics/dataset-statistics.component';
import { MediaFiltering } from './media-filtering/media-filtering.component';
import { MediaUpload } from './media-upload.component';
import { TotalItems } from './total-items.component';
import { toggleMultipleSelection } from './util';

type ToolbarProps = {
    items: Media[];
    viewMode: ViewModes;
    setViewMode: Dispatch<SetStateAction<ViewModes>>;
};

type AnnotateButtonProps = {
    isDisabled?: boolean;
    onClick?: () => void;
};

const AnnotateButton = ({ isDisabled, onClick }: AnnotateButtonProps) => {
    return (
        <Button margin={0} variant={'primary'} onPress={onClick} isDisabled={isDisabled}>
            Annotate
        </Button>
    );
};

const SortMediaByUploadDate = () => {
    const { sortDirection, setSortDirection } = useDatasetFiltersSearchParams();

    if (sortDirection === 'asc') {
        return (
            <ActionButton isQuiet onPress={() => setSortDirection('desc')}>
                Oldest first <SortUp />
            </ActionButton>
        );
    }

    return (
        <ActionButton isQuiet onPress={() => setSortDirection('asc')}>
            Newest first <SortDown />
        </ActionButton>
    );
};

export const Toolbar = ({ items, viewMode, setViewMode }: ToolbarProps) => {
    const { onSelectedMediaItemChange } = useSelectDatasetItem();
    const { selectedKeys, setSelectedKeys, toggleSelectedKeys } = useSelectedData();

    const selectedMediaItems = selectedKeys instanceof Set ? selectedKeys : null;

    const totalSelectedElements = selectedMediaItems?.size ?? 0;
    const hasSelectedElements = totalSelectedElements > 0;

    const handleToggleManyItemSelection = () => {
        const images = items.map((item) => String(item.id));
        setSelectedKeys(toggleMultipleSelection(images));
    };

    const selectedImagesIds = useMemo(() => {
        if (selectedMediaItems === null) return [];

        return Array.from(selectedMediaItems)
            .filter((itemId) => items.some((item) => itemId === item.id && isImage(item)))
            .filter((itemId) => isString(itemId));
    }, [selectedMediaItems, items]);

    const noMediaSelected = selectedMediaItems?.size === 0;

    return (
        <Flex direction={'column'} gridArea={'toolbar'} gap={'size-200'} marginBottom={'size-200'}>
            <Flex alignItems={'center'} justifyContent={'end'}>
                <ButtonGroup UNSAFE_style={{ gap: dimensionValue('size-125') }}>
                    {noMediaSelected && <ImportExport />}

                    <MediaUpload />

                    <AssignLabel selectedImagesIds={selectedImagesIds} />

                    {noMediaSelected && <TrainModel />}

                    {noMediaSelected && (
                        <AnnotateButton
                            isDisabled={items.at(0) === undefined}
                            onClick={items.at(0) === undefined ? undefined : () => onSelectedMediaItemChange(items[0])}
                        />
                    )}
                </ButtonGroup>
            </Flex>

            <Divider size='S' />

            <Flex direction={'row'} alignItems={'center'} justifyContent={'space-between'}>
                <Flex
                    gap={'size-50'}
                    height={'size-400'}
                    direction={'row'}
                    alignItems={'center'}
                    justifyContent={'space-between'}
                >
                    <Checkbox
                        aria-label={'select all'}
                        onChange={handleToggleManyItemSelection}
                        isSelected={hasSelectedElements && totalSelectedElements === items.length}
                    />

                    {!hasSelectedElements && <SortMediaByUploadDate />}

                    <Divider orientation={'vertical'} size={'S'} />

                    {hasSelectedElements && (
                        <DeleteMediaItem
                            itemsIds={Array.from(selectedKeys) as string[]}
                            onDeleted={toggleSelectedKeys}
                        />
                    )}
                </Flex>

                <Flex gap={'size-200'} alignItems={'center'}>
                    <TotalItems totalSelectedElements={totalSelectedElements} />

                    {noMediaSelected && (
                        <>
                            <MediaFiltering />

                            <DatasetStatistics />

                            <MediaViewModes
                                viewMode={viewMode}
                                setViewMode={setViewMode}
                                items={[ViewModes.LARGE, ViewModes.MEDIUM, ViewModes.SMALL]}
                            />
                        </>
                    )}
                </Flex>
            </Flex>

            <Divider size='S' />
        </Flex>
    );
};
