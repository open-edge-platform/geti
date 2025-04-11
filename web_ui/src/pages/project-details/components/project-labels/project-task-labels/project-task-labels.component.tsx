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

import { Flex, Text } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';
import noop from 'lodash/noop';

import { LabelTreeItem, LabelTreeLabelProps, Readonly } from '../../../../../core/labels/label-tree-view.interface';
import { DOMAIN } from '../../../../../core/projects/core.interface';
import { TaskMetadata } from '../../../../../core/projects/task.interface';
import { DomainName } from '../../../../../shared/components/domain-name/domain-name.component';
import { ProjectLabelsManagement } from '../project-labels-management/project-labels-management.component';

import classes from './project-task-labels.module.scss';

interface ReadonlyProjectTaskLabelsProps {
    task: TaskMetadata;
    isTaskChainProject: boolean;
    type: Readonly.YES;
}

interface EditableProjectTaskLabelsProps {
    task: TaskMetadata;
    isTaskChainProject: boolean;
    isInEdition: boolean;
    editLabels: (labels: LabelTreeItem[], domain: DOMAIN) => void;
    parentLabel: LabelTreeLabelProps | undefined;
    setLabelsValidity: (isValid: boolean) => void;
}

type ProjectTaskLabelsProps = EditableProjectTaskLabelsProps | ReadonlyProjectTaskLabelsProps;

export const ProjectTaskLabels = ({ task, isTaskChainProject, ...props }: ProjectTaskLabelsProps): JSX.Element => {
    const { labels, relation, domain } = task;
    const isInEdition = 'isInEdition' in props ? props.isInEdition : false;
    const editLabels = 'editLabels' in props ? props.editLabels : noop;
    const setLabelsValidity = 'setLabelsValidity' in props ? props.setLabelsValidity : noop;
    const parentLabel = 'parentLabel' in props ? props.parentLabel : undefined;
    const firstTask = isEmpty(parentLabel);

    return (
        <Flex direction={'column'} gap={'size-100'}>
            {isTaskChainProject && (
                <Text UNSAFE_className={classes.title}>
                    <DomainName domain={domain} />
                </Text>
            )}
            <ProjectLabelsManagement
                isInEdition={isInEdition}
                setIsDirty={noop}
                labelsTree={labels}
                setLabelsTree={(newLabels) => editLabels(newLabels, task.domain)}
                relation={relation}
                isTaskChainProject={isTaskChainProject}
                parentLabel={parentLabel}
                domains={[domain]}
                newItemNotAllowed={isTaskChainProject && firstTask}
                id={domain.toLowerCase()}
                setLabelsValidity={setLabelsValidity}
            />
        </Flex>
    );
};
