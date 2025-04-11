// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';

import { idMatchingFormat } from '../../../../../test-utils/id-utils';
import { Accordion } from '../../../accordion/accordion.component';
import { SelectableManyTasksProps } from '../selectable-many-tasks.interface';
import { SelectableTab } from '../selectable-tab/selectable-tab.component';

import classes from './selectable-tabs-list.module.scss';

type SelectableTabsListProps = Omit<SelectableManyTasksProps, 'selectedComponent' | 'updateParameter'>;

export const SelectableTabsList = ({
    configurableParameters,
    selectedComponentId,
    setSelectedComponentId,
}: SelectableTabsListProps): JSX.Element => {
    return (
        <Flex direction={'column'} height={'100%'} UNSAFE_style={{ overflowY: 'auto' }} minWidth={'24rem'}>
            {configurableParameters.map(({ taskTitle, taskId, components }, index) => {
                return (
                    <Accordion
                        key={taskId}
                        header={<Text UNSAFE_style={{ paddingRight: dimensionValue('size-50') }}>{taskTitle}</Text>}
                        idPrefix={idMatchingFormat(taskTitle)}
                        defaultOpenState={index === 0}
                        isFullHeight={false}
                        UNSAFE_className={classes.selectableTabAccordion}
                    >
                        {components.map((component) => (
                            <SelectableTab
                                key={component.id}
                                component={component}
                                isSelected={selectedComponentId === component.id}
                                setSelectedComponentId={setSelectedComponentId}
                            />
                        ))}
                    </Accordion>
                );
            })}
        </Flex>
    );
};
