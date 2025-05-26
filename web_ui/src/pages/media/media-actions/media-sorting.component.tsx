// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Key } from 'react';

import { Icon, Item, Menu, MenuTrigger as MenuTriggerSpectrum, Section, Text } from '@geti/ui';
import { SortDown, SortUp, SortUpDown } from '@geti/ui/icons';
import { isEmpty } from 'lodash-es';

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
        setSortingOptions({ sortBy: sortBy.toUpperCase(), sortDir: sortDir === 'asc' ? 'asc' : 'dsc' });
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
