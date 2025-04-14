// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
