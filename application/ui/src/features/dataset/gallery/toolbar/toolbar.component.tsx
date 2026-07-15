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
    Item,
    MediaViewModes,
    Menu,
    MenuTrigger,
    Selection,
    ViewModes,
} from '@geti-ui/ui';
import { SortDown, SortUp } from '@geti-ui/ui/icons';
import { useDatasetFiltersSearchParams } from 'hooks/use-dataset-filters-search-params.hook';
import { isString } from 'lodash-es';

import type { SortDirection } from '../../../../hooks/sort-direction.interface';
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

const SORT_OPTIONS: { key: SortDirection; label: string }[] = [
    { key: 'desc', label: 'Newest first' },
    { key: 'asc', label: 'Oldest first' },
];

const SortMediaByUploadDate = () => {
    const { sortDirection, setSortDirection } = useDatasetFiltersSearchParams();

    const handleSelectionChange = (keys: Selection) => {
        if (keys === 'all') return;

        const [key] = Array.from(keys);

        if (key === 'asc' || key === 'desc') {
            setSortDirection(key);
        }
    };

    return (
        <MenuTrigger>
            <ActionButton isQuiet aria-label='Sort by upload date'>
                {sortDirection === 'asc' ? (
                    <SortUp width={'var(--icon-size)'} height={'var(--icon-size)'} />
                ) : (
                    <SortDown
                        width={'var(--spectrum-global-dimension-size-300)'}
                        height={'var(--spectrum-global-dimension-size-300)'}
                    />
                )}
            </ActionButton>
            <Menu
                selectionMode='single'
                disallowEmptySelection
                selectedKeys={[sortDirection]}
                onSelectionChange={handleSelectionChange}
            >
                {SORT_OPTIONS.map((option) => (
                    <Item key={option.key}>{option.label}</Item>
                ))}
            </Menu>
        </MenuTrigger>
    );
};

export const Toolbar = ({ items, viewMode, setViewMode }: ToolbarProps) => {
    const { onSelectedMediaItemChange } = useSelectDatasetItem();
    const { selectedKeys, setSelectedKeys } = useSelectedData();

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
            <Flex direction={'row'} alignItems={'center'} justifyContent={'space-between'}>
                <Flex gap={'size-125'} height={'size-400'} direction={'row'} alignItems={'center'}>
                    <Flex gap={'size-100'} direction={'row'} alignItems={'center'}>
                        <Checkbox
                            aria-label={'select all'}
                            onChange={handleToggleManyItemSelection}
                            isSelected={hasSelectedElements && totalSelectedElements === items.length}
                        />

                        <TotalItems totalSelectedElements={totalSelectedElements} />
                    </Flex>

                    <Divider orientation={'vertical'} size={'S'} />

                    <SortMediaByUploadDate />

                    {hasSelectedElements && (
                        <DeleteMediaItem
                            itemsIds={Array.from(selectedKeys) as string[]}
                            onDeleted={() => setSelectedKeys(new Set())}
                            isDisabled={items.length === 0}
                        />
                    )}

                    {noMediaSelected && (
                        <>
                            <MediaFiltering />

                            <DatasetStatistics />

                            <MediaViewModes
                                viewMode={viewMode}
                                setViewMode={setViewMode}
                                items={[ViewModes.LARGE, ViewModes.MEDIUM, ViewModes.SMALL]}
                            />

                            <Divider orientation={'vertical'} size={'S'} />

                            <ImportExport />

                            <MediaUpload />
                        </>
                    )}
                </Flex>

                <ButtonGroup UNSAFE_style={{ gap: dimensionValue('size-125') }}>
                    {hasSelectedElements && <AssignLabel selectedImagesIds={selectedImagesIds} />}

                    {noMediaSelected && (
                        <AnnotateButton
                            isDisabled={items.at(0) === undefined}
                            onClick={items.at(0) === undefined ? undefined : () => onSelectedMediaItemChange(items[0])}
                        />
                    )}

                    {noMediaSelected && <TrainModel />}
                </ButtonGroup>
            </Flex>

            <Divider size='S' />
        </Flex>
    );
};
