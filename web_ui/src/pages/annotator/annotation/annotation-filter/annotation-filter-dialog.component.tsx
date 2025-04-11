// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { CSSProperties } from 'react';

import { Content, Dialog, Flex, Heading, Text, View } from '@adobe/react-spectrum';
import { dimensionValue, useMediaQuery } from '@react-spectrum/utils';
import isEmpty from 'lodash/isEmpty';

import { Label } from '../../../../core/labels/label.interface';
import { ActionButton } from '../../../../shared/components/button/button.component';
import { Checkbox } from '../../../../shared/components/checkbox/checkbox.component';
import { isLargeSizeQuery } from '../../../../theme/queries';
import { BaseLabelSearch } from '../../components/labels/label-search/base-label-search.component';
import { useTaskChainOutput } from '../../providers/task-chain-provider/use-task-chain-output.hook';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { useAnnotationFilters } from './use-annotation-filters.hook';
import { useTaskLabels } from './use-task-labels.hook';

import classes from './annotation-filter-trigger.module.scss';

const paddingStyle = {
    '--spectrum-dialog-padding-x': dimensionValue('size-300'),
    '--spectrum-dialog-padding-y': dimensionValue('size-300'),
} as CSSProperties;
const tabletPaddingStyle = {
    '--spectrum-dialog-padding-x': dimensionValue('size-150'),
    '--spectrum-dialog-padding-y': dimensionValue('size-150'),
} as CSSProperties;

export const AnnotationFilterDialog = () => {
    const [filters, setFilters] = useAnnotationFilters();
    const isAnnotationsFilterEmpty = isEmpty(filters);
    const handleClearAll = () => {
        setFilters([]);
    };

    const isLargeSize = useMediaQuery(isLargeSizeQuery);

    const { selectedTask, tasks } = useTask();
    const labels = useTaskLabels();

    const selectLabel = (label: Label | null) => {
        if (label === null) {
            return;
        }

        const hasFilterForLabel = filters.find((id) => label.id === id);

        if (hasFilterForLabel) {
            setFilters(filters.filter((id) => id !== label.id));
        } else {
            setFilters([...filters, label.id]);
        }
    };

    const totalMatches = useTaskChainOutput(tasks, selectedTask).length;

    return (
        <Dialog width={{ base: '60rem', L: '66rem' }} UNSAFE_style={isLargeSize ? paddingStyle : tabletPaddingStyle}>
            <Heading UNSAFE_className={classes.filterPanelHeader} marginBottom='size-350'>
                <Text id='filter-dialog-title'>Show annotations matching the following labels</Text>

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
                        <Flex alignItems={'center'} justifyContent={'center'}>
                            <Text UNSAFE_className={classes.filterPanelMatches} id={'label-filter-matches'}>
                                {totalMatches} match{totalMatches == 1 ? '' : 'es'}
                            </Text>
                        </Flex>
                    </View>

                    <ActionButton
                        isQuiet
                        id='filter-dialog-clear-all'
                        onPress={handleClearAll}
                        isDisabled={isAnnotationsFilterEmpty}
                    >
                        Clear All
                    </ActionButton>
                </Flex>
            </Heading>
            <Content>
                <BaseLabelSearch
                    labels={labels}
                    onClick={selectLabel}
                    prefix={(label) => {
                        return (
                            <Checkbox
                                id={`select-label-filter-${label.id}`}
                                aria-label={`Select label filter for ${label.name}`}
                                isSelected={filters.find((id) => id === label.id) !== undefined}
                                onChange={() => selectLabel(label)}
                            />
                        );
                    }}
                />
            </Content>
        </Dialog>
    );
};
