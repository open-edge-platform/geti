// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useCallback, useEffect, useRef, useState } from 'react';

import { CustomPopover, SearchField, Tooltip, TooltipTrigger, View } from '@geti/ui';
import { Search } from '@geti/ui/icons';
import { useOverlayTriggerState } from '@react-stately/overlays';
import { isEmpty } from 'lodash-es';

import { AdvancedFilterOptions } from '../../../core/media/media-filter.interface';
import { useDebouncedCallback } from '../../../hooks/use-debounced-callback/use-debounced-callback.hook';
import { QuietToggleButton } from '../../../shared/components/quiet-button/quiet-toggle-button.component';
import { SEARCH_MEDIA_LABEL } from '../../project-details/components/project-media/utils';
import { addOrUpdateFilterRule, buildSearchRule, getSearchRuleValue, removeFilterRule } from '../utils';

interface MediaSearchProps {
    mediaFilterOptions: AdvancedFilterOptions;
    setMediaFilterOptions: (options: AdvancedFilterOptions) => void;
    isDisabled?: boolean;
    id?: string;
}

export const MediaSearch = ({
    mediaFilterOptions,
    setMediaFilterOptions,
    isDisabled = false,
    id = '',
}: MediaSearchProps): JSX.Element => {
    const triggerRef = useRef(null);
    const dialogState = useOverlayTriggerState({});

    const [searchText, setSearchText] = useState<string>('');

    const SEARCH_BUTTON_TEST_ID = `${!isEmpty(id) ? `${id}-` : ''}search-media-button-id`;
    const SEARCH_FIELD_TEST_ID = `${!isEmpty(id) ? `${id}-` : ''}search-field-media-id`;

    useEffect(() => {
        const searchRuleValue = getSearchRuleValue(mediaFilterOptions);
        //search saved in url params should be applied to search input
        //If filter is removed it should clear search input
        //When search field is open it should not update searchText
        searchRuleValue !== searchText && !dialogState.isOpen && setSearchText(searchRuleValue);

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [mediaFilterOptions]);

    const setFilterByMediaName = useCallback(
        (newValue: string): void => {
            const newRule = buildSearchRule(newValue);

            if (newValue === '') {
                const updatedFilterRules = removeFilterRule(mediaFilterOptions, newRule);

                setMediaFilterOptions(updatedFilterRules);
            } else {
                setMediaFilterOptions(addOrUpdateFilterRule(mediaFilterOptions, newRule));
            }
        },
        [mediaFilterOptions, setMediaFilterOptions]
    );

    const debouncedFilterByMediaName = useDebouncedCallback(setFilterByMediaName, 300);

    const onSubmit = (searchInput: string, options = { minLength: 0, debounced: false }): void => {
        const mediaName = searchInput.trim();
        const { minLength, debounced } = options;

        setSearchText(searchInput);

        if (mediaName.length >= minLength || isEmpty(mediaName)) {
            debounced ? debouncedFilterByMediaName(mediaName) : setFilterByMediaName(mediaName);
        }
    };

    const onSearchChange = (text: string): void => {
        onSubmit(text, { minLength: 3, debounced: true });
    };

    const onClearField = (): void => {
        onSubmit('');
    };

    return (
        <>
            <TooltipTrigger placement={'bottom'}>
                <QuietToggleButton
                    isQuiet
                    key='search'
                    justifySelf='end'
                    id={SEARCH_BUTTON_TEST_ID}
                    data-testid={SEARCH_BUTTON_TEST_ID}
                    ref={triggerRef}
                    isDisabled={isDisabled}
                    aria-label={SEARCH_MEDIA_LABEL}
                    onPress={() => dialogState.toggle()}
                    isSelected={dialogState.isOpen}
                >
                    <Search />
                </QuietToggleButton>
                <Tooltip>{SEARCH_MEDIA_LABEL}</Tooltip>
            </TooltipTrigger>

            <CustomPopover state={dialogState} ref={triggerRef}>
                <View padding='size-300'>
                    <SearchField
                        type='search'
                        width='size-3400'
                        inputMode='search'
                        aria-label='media search'
                        id={SEARCH_FIELD_TEST_ID}
                        data-testid={SEARCH_FIELD_TEST_ID}
                        placeholder='Search by file name'
                        value={searchText}
                        isDisabled={isDisabled}
                        onSubmit={onSubmit}
                        onClear={onClearField}
                        onChange={onSearchChange}
                        // eslint-disable-next-line jsx-a11y/no-autofocus
                        autoFocus
                        maxLength={255}
                    />
                </View>
            </CustomPopover>
        </>
    );
};
