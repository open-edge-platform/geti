// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';

import { LabelTreeItem } from '../../../core/labels/label-tree-view.interface';
import { Label } from '../../../core/labels/label.interface';
import { TaskMetadata } from '../../../core/projects/task.interface';
import { isNonEmptyArray } from '../../utils';
import { DomainName } from '../domain-name/domain-name.component';
import { SearchLabelTreeItemSuffix, TaskLabelTreeItem } from './task-label-tree-item.component';
import { groupTitleStyles, VIEW_GAP } from './utils';

interface TaskLabelTreeContainerProps {
    level?: number;
    ariaLabel?: string;
    tasksMetadata: TaskMetadata[];
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
    onClick?: (label: Label) => void;
}

interface TaskLabelTreeViewProps {
    level?: number;
    labelTreeItems: LabelTreeItem[];
    suffix?: SearchLabelTreeItemSuffix;
    prefix?: SearchLabelTreeItemSuffix;
    onClick?: (label: Label) => void;
}

const TaskLabelTreeView = (props: TaskLabelTreeViewProps): JSX.Element => {
    const { labelTreeItems, level = -1 } = props;
    const currentLevel = level + 1;

    return (
        <ul>
            {labelTreeItems.map((label) => (
                <TaskLabelTreeItem key={label.id} {...props} label={label} level={currentLevel}>
                    {isNonEmptyArray(label.children) && (
                        <TaskLabelTreeView {...props} level={currentLevel} labelTreeItems={label.children} />
                    )}
                </TaskLabelTreeItem>
            ))}
        </ul>
    );
};

export const TaskLabelTreeContainer = (props: TaskLabelTreeContainerProps): JSX.Element => {
    return (
        <div aria-label={props.ariaLabel} style={{ overflow: 'auto', overflowX: 'hidden', width: '100%' }}>
            {isNonEmptyArray(props.tasksMetadata) ? (
                <Flex gap={'size-300'} direction={'column'}>
                    {props.tasksMetadata.map(({ domain, labels }, _, tasks) => {
                        const isTaskChain = tasks.length > 1;

                        return (
                            <View key={`filter-metadata-${domain}`}>
                                {isTaskChain && (
                                    <Text UNSAFE_style={groupTitleStyles} marginStart={dimensionValue(VIEW_GAP)}>
                                        <DomainName domain={domain} />
                                    </Text>
                                )}
                                <TaskLabelTreeView {...props} labelTreeItems={labels} />
                            </View>
                        );
                    })}
                </Flex>
            ) : (
                <Flex alignItems='center' justifyContent='center' marginTop='size-100' marginBottom='size-100'>
                    <Text>No Results</Text>
                </Flex>
            )}
        </div>
    );
};
