// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Key } from 'react';

import { Icon, Item, Menu, MenuTrigger as MenuTriggerSpectrum, Section, Text } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { SortDown, SortUp, SortUpDown } from '../../../assets/icons';
import { AdvancedFilterSortingOptions, SortMenuActionKey } from '../../../core/media/media-filter.interface';
import { ButtonWithSpectrumTooltip } from '../../../shared/components/button-with-tooltip/button-with-tooltip.component';
import { idMatchingFormat } from '../../../test-utils/id-utils';
import { SORT_MEDIA_LABEL } from '../../project-details/components/project-media/utils';

interface MediaSortingProps {
    isDisabled?: boolean;
    sortingOptions: AdvancedFilterSortingOptions;
    setSortingOptions: (options: AdvancedFilterSortingOptions) => void;
}

const KEY_SEPARATOR = '_';

const getKey = (name: string, direction: string) => `${name.toLocaleLowerCase()}${KEY_SEPARATOR}${direction}`;

export const MediaSorting = ({
    isDisabled = false,
    sortingOptions,
    setSortingOptions,
}: MediaSortingProps): JSX.Element => {
    const selectedKey = !isEmpty(sortingOptions)
        ? `${getKey(sortingOptions.sortBy ?? '', sortingOptions.sortDir ?? '')}`
        : '';

    const onSortMenuAction = (key: Key) => {
        const [sortBy, sortDir] = String(key).split(KEY_SEPARATOR);
        setSortingOptions({ sortBy: sortBy.toUpperCase(), sortDir });
    };

    return (
        <MenuTriggerSpectrum>
            <ButtonWithSpectrumTooltip
                isQuiet
                isClickable
                id='sort-media-action-menu'
                isDisabled={isDisabled}
                aria-label={SORT_MEDIA_LABEL}
                tooltip={SORT_MEDIA_LABEL}
                tooltipPlacement={'bottom'}
            >
                <SortUpDown />
            </ButtonWithSpectrumTooltip>

            <Menu selectionMode='single' onAction={onSortMenuAction} defaultSelectedKeys={[selectedKey]}>
                <Section>
                    <Item key={`${getKey(SortMenuActionKey.NAME, 'asc')}`} textValue={SortMenuActionKey.NAME}>
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.NAME, 'asc'))}>Name</Text>
                        <Icon>
                            <SortUp />
                        </Icon>
                    </Item>
                    <Item key={`${getKey(SortMenuActionKey.NAME, 'dsc')}`} textValue={SortMenuActionKey.NAME}>
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.NAME, 'dsc'))}>Name</Text>
                        <Icon>
                            <SortDown />
                        </Icon>
                    </Item>
                </Section>
                <Section>
                    <Item key={`${getKey(SortMenuActionKey.DATE, 'asc')}`} textValue={SortMenuActionKey.DATE}>
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.DATE, 'asc'))}>Upload Date</Text>
                        <Icon>
                            <SortUp />
                        </Icon>
                    </Item>
                    <Item key={`${getKey(SortMenuActionKey.DATE, 'dsc')}`} textValue={SortMenuActionKey.DATE}>
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.DATE, 'dsc'))}>Upload Date</Text>
                        <Icon>
                            <SortDown />
                        </Icon>
                    </Item>
                </Section>
                <Section>
                    <Item key={`${getKey(SortMenuActionKey.SIZE, 'asc')}`} textValue={SortMenuActionKey.SIZE}>
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.SIZE, 'asc'))}>File size</Text>
                        <Icon>
                            <SortUp />
                        </Icon>
                    </Item>
                    <Item key={`${getKey(SortMenuActionKey.SIZE, 'dsc')}`} textValue={SortMenuActionKey.SIZE}>
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.SIZE, 'dsc'))}>File size</Text>
                        <Icon>
                            <SortDown />
                        </Icon>
                    </Item>
                </Section>
                <Section>
                    <Item
                        key={`${getKey(SortMenuActionKey.ANNOTATION_DATE, 'asc')}`}
                        textValue={SortMenuActionKey.ANNOTATION_DATE}
                    >
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.ANNOTATION_DATE, 'asc'))}>
                            Annotation date
                        </Text>
                        <Icon>
                            <SortUp />
                        </Icon>
                    </Item>
                    <Item
                        key={`${getKey(SortMenuActionKey.ANNOTATION_DATE, 'dsc')}`}
                        textValue={SortMenuActionKey.ANNOTATION_DATE}
                    >
                        <Text id={idMatchingFormat(getKey(SortMenuActionKey.ANNOTATION_DATE, 'dsc'))}>
                            Annotation date
                        </Text>
                        <Icon>
                            <SortDown />
                        </Icon>
                    </Item>
                </Section>
            </Menu>
        </MenuTriggerSpectrum>
    );
};
