// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue, Flex, Text } from '@geti/ui';

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
