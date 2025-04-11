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

import { Divider, Flex, View } from '@adobe/react-spectrum';

import { SelectableManyTasksProps } from './selectable-many-tasks.interface';
import { SelectableTabsList } from './selectable-tabs-list/selectable-tabs-list.component';
import { SelectableTabContent } from './selected-tab-content/selectable-tab-content.component';

import classes from './selectable-many-tasks.module.scss';

export const SelectableManyTasks = ({
    configurableParameters,
    setSelectedComponentId,
    selectedComponentId,
    selectedComponent,
    updateParameter,
}: SelectableManyTasksProps): JSX.Element => {
    return (
        <View padding={'size-250'} paddingEnd={0} height={'100%'} UNSAFE_className={classes.configParametersBox}>
            <Flex height={'100%'}>
                <SelectableTabsList
                    configurableParameters={configurableParameters}
                    selectedComponentId={selectedComponentId}
                    setSelectedComponentId={setSelectedComponentId}
                />
                <Divider size={'S'} orientation={'vertical'} />
                <SelectableTabContent selectedComponent={selectedComponent} updateParameter={updateParameter} />
            </Flex>
        </View>
    );
};
