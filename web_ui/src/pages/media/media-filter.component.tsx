// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, Dispatch, MutableRefObject, useCallback, useEffect, useReducer, useRef, useState } from 'react';

import {
    ActionButton,
    ButtonGroup,
    Content,
    Dialog,
    DialogTrigger,
    dimensionValue,
    Flex,
    Heading,
    Text,
    Tooltip,
    TooltipTrigger,
    useMediaQuery,
    useUnwrapDOMRef,
    View,
    type FocusableRefValue,
} from '@geti/ui';
import { Add, Filter } from '@geti/ui/icons';
import { isEmpty, isEqual } from 'lodash-es';
import { v4 as uuidv4 } from 'uuid';

import { isLargeSizeQuery } from '../../../packages/ui/theme/queries';
import {
    AdvancedFilterOptions,
    SearchOptionsActions,
    SearchOptionsActionsType,
    SearchOptionsRule,
    SearchRuleField,
} from '../../core/media/media-filter.interface';
import { ColorMode } from '../../shared/components/quiet-button/quiet-action-button.component';
import { QuietToggleButton } from '../../shared/components/quiet-button/quiet-toggle-button.component';
import { ThreeDotsFlashing } from '../../shared/components/three-dots-flashing/three-dots-flashing.component';
import { FILTER_MEDIA_LABEL } from '../project-details/components/project-media/utils';
import { MediaFilterRow } from './components/media-filter-row.component';
import { SearchOptionReducer } from './reducers/search-options-reducer';
import { getRuleByField, getUpdatedRule, getValidRules, hasOnlyOneRuleAndIsEmpty, isEmptyRule } from './utils';

import classes from './media-filter.module.scss';

interface MediaFilterProps {
    totalMatches: number;
    isDisabled?: boolean;
    isMediaFetching: boolean;
    isMediaFilterEmpty: boolean;
    isDatasetAccordion?: boolean;
    disabledFilterRules?: SearchRuleField[];
    filterOptions: AdvancedFilterOptions;
    onSetFilterOptions: (options: AdvancedFilterOptions) => void;
    id?: string;
}
// The user can filter by name outside this component, this hook dispatches actions to add that search as a filter rule
const useSetFilterByName = (
    filterOptions: AdvancedFilterOptions,
    state: AdvancedFilterOptions,
    dispatch: Dispatch<SearchOptionsActions>,
    canCallFilter: MutableRefObject<boolean>
) => {
    useEffect(() => {
        const searchByNameRule = getRuleByField(filterOptions.rules, SearchRuleField.MediaName);

        if ((isEqual(state, filterOptions) || hasOnlyOneRuleAndIsEmpty(state?.rules)) && isEmpty(searchByNameRule)) {
            return;
        }

        if (searchByNameRule.some(isEmptyRule)) {
            dispatch({ type: SearchOptionsActionsType.REMOVE_ALL });
        } else {
            canCallFilter.current = false;
            dispatch({ type: SearchOptionsActionsType.UPDATE_ALL, filterOptions });
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [filterOptions]);
};

const initialFilterOptions: AdvancedFilterOptions = {
    condition: undefined,
    rules: [{ id: uuidv4(), value: '', operator: '', field: '' }],
};

const paddingStyle = {
    '--spectrum-dialog-padding-x': dimensionValue('size-300'),
    '--spectrum-dialog-padding-y': dimensionValue('size-300'),
} as CSSProperties;
const tabletPaddingStyle = {
    '--spectrum-dialog-padding-x': dimensionValue('size-150'),
    '--spectrum-dialog-padding-y': dimensionValue('size-150'),
} as CSSProperties;

export const MediaFilter = ({
    totalMatches,
    filterOptions,
    isMediaFetching,
    onSetFilterOptions,
    isMediaFilterEmpty,
    isDisabled = false,
    isDatasetAccordion = false,
    disabledFilterRules,
    id,
}: MediaFilterProps): JSX.Element => {
    const canCallFilter = useRef<boolean>(false);
    const isLargeSize = useMediaQuery(isLargeSizeQuery);
    const filterButtonRef = useRef<FocusableRefValue<HTMLButtonElement>>(null);
    const [state, dispatch] = useReducer(SearchOptionReducer, { ...initialFilterOptions, ...filterOptions });
    const unwrappedFilterButtonRef = useUnwrapDOMRef(filterButtonRef);
    const [isOpen, setIsOpen] = useState(false);

    useSetFilterByName(filterOptions, state, dispatch, canCallFilter);

    useEffect(() => {
        const validRules = getValidRules(state?.rules);

        if (canCallFilter.current && !isEqual(validRules, filterOptions.rules)) {
            if (!isEmpty(validRules)) {
                onSetFilterOptions({ condition: 'and', rules: validRules });
            } else if (isEmpty(state?.rules) && !isEmpty(filterOptions)) {
                onSetFilterOptions({});
            }
        }

        canCallFilter.current = true;

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [state.rules, onSetFilterOptions]);

    useEffect(() => {
        unwrappedFilterButtonRef.current?.scrollIntoView();

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [state.rules]);

    const onUpdate = useCallback((itemId: string, updatedRule: SearchOptionsRule) => {
        canCallFilter.current = true;

        dispatch({ type: SearchOptionsActionsType.UPDATE, id: itemId, rule: getUpdatedRule(updatedRule) });
    }, []);

    const onReset = useCallback((itemId: string) => {
        canCallFilter.current = false;
        dispatch({ type: SearchOptionsActionsType.RESET, id: itemId });
    }, []);

    const onRemove = useCallback((itemId: string) => {
        canCallFilter.current = true;

        dispatch({ type: SearchOptionsActionsType.REMOVE, id: itemId });
    }, []);

    return (
        <DialogTrigger hideArrow type='popover' onOpenChange={setIsOpen}>
            <TooltipTrigger placement={'bottom'}>
                <QuietToggleButton
                    id='modal-trigger'
                    data-testid={`${!isEmpty(id) ? `${id}-` : ''}filter-media-button`}
                    isSelected={isOpen}
                    isDisabled={isDisabled}
                    aria-label={FILTER_MEDIA_LABEL}
                >
                    <Filter />
                </QuietToggleButton>
                <Tooltip>{FILTER_MEDIA_LABEL}</Tooltip>
            </TooltipTrigger>
            <Dialog
                width={{ base: '60rem', L: '66rem' }}
                UNSAFE_style={isLargeSize ? paddingStyle : tabletPaddingStyle}
            >
                <Heading
                    UNSAFE_className={classes.filterPanelHeader}
                    marginBottom={!isEmpty(state?.rules) ? 'size-350' : 0}
                >
                    <Text id='filter-dialog-title'>Show results matching of all the following criteria</Text>

                    {!isMediaFilterEmpty ? (
                        <Flex alignItems={'center'}>
                            <View
                                paddingX={'size-200'}
                                paddingY={'size-25'}
                                backgroundColor={'gray-700'}
                                borderRadius={'large'}
                                borderWidth={'thin'}
                                borderColor={'gray-700'}
                                minWidth={'size-1200'}
                            >
                                <Flex
                                    alignItems={'center'}
                                    gap={isMediaFetching ? 'size-100' : ''}
                                    justifyContent={'center'}
                                >
                                    {isMediaFetching && (
                                        <View paddingTop={'size-65'}>
                                            <ThreeDotsFlashing mode={ColorMode.LIGHT} size={'S'} />
                                        </View>
                                    )}

                                    <Text UNSAFE_className={classes.filterPanelMatches}>
                                        {!isMediaFetching && totalMatches} match{totalMatches == 1 ? '' : 'es'}
                                    </Text>
                                </Flex>
                            </View>

                            <ActionButton
                                isQuiet
                                id='filter-dialog-clear-all'
                                onPress={() => dispatch({ type: SearchOptionsActionsType.REMOVE_ALL })}
                            >
                                Clear All
                            </ActionButton>
                        </Flex>
                    ) : null}
                </Heading>
                {!isEmpty(state?.rules) && (
                    <Content>
                        <div role='list' aria-label='Filter rules'>
                            {state.rules.map((rule) => (
                                <div role='listitem' key={rule.id} className={classes.rowBody}>
                                    <MediaFilterRow
                                        rule={rule}
                                        onUpdate={onUpdate}
                                        onRemove={onRemove}
                                        onReset={onReset}
                                        isDatasetAccordion={isDatasetAccordion}
                                        disabledFilterRules={disabledFilterRules}
                                    />
                                </div>
                            ))}
                        </div>
                    </Content>
                )}

                <ButtonGroup UNSAFE_className={classes.dialogFooter}>
                    <ActionButton
                        isQuiet
                        marginEnd='auto'
                        ref={filterButtonRef}
                        onPress={() => {
                            canCallFilter.current = false;
                            dispatch({ type: SearchOptionsActionsType.ADD });
                        }}
                    >
                        <Add id='filter-dialog-new-filter' className={classes.addIcon} /> <Text>New filter</Text>
                    </ActionButton>
                </ButtonGroup>
            </Dialog>
        </DialogTrigger>
    );
};
