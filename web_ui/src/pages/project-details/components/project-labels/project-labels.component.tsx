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

import { Fragment, useCallback, useEffect, useState } from 'react';

import { DialogContainer, Divider, Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import isEmpty from 'lodash/isEmpty';

import { LabelTreeItem, LabelTreeLabelProps } from '../../../../core/labels/label-tree-view.interface';
import { getFlattenedLabels } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { useProjectActions } from '../../../../core/projects/hooks/use-project-actions.hook';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { useHistoryBlock } from '../../../../hooks/use-history-block/use-history-block.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { Button } from '../../../../shared/components/button/button.component';
import { isNew } from '../../../../shared/components/label-tree-view/label-tree-view-item/utils';
import { Loading } from '../../../../shared/components/loading/loading.component';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
import { UnsavedChangesDialog } from '../../../../shared/components/unsaved-changes-dialog/unsaved-changes-dialog.component';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { ProjectTaskLabels } from './project-task-labels/project-task-labels.component';
import { RevisitAlertDialog } from './revisit-alert-dialog/revisit-alert-dialog.component';
import { getTasksMetadata } from './utils';

export const ProjectLabels = (): JSX.Element => {
    const { editProjectLabelsMutation } = useProjectActions();
    const datasetIdentifier = useDatasetIdentifier();

    const { project, isTaskChainProject, reload } = useProject();

    const [isDirty, setIsDirty] = useState<boolean>(false);
    const [isDialogOpen, setDialogOpen] = useState<boolean>(false);
    const [isEditionEnabled, setEditionEnablement] = useState<boolean>(false);
    const [tasksMetadata, setTasksMetadata] = useState<TaskMetadata[]>(getTasksMetadata(project.tasks));
    const [labelsValid, setLabelsValidity] = useState<boolean>(true);

    const { addNotification } = useNotification();

    const [isOpen, setIsOpen, onUnsavedAction] = useHistoryBlock(isEditionEnabled);

    useEffect(() => {
        setTasksMetadata(getTasksMetadata(project.tasks));
    }, [project]);

    const editToggle = () => {
        setEditionEnablement(!isEditionEnabled);

        if (isEditionEnabled) {
            setIsDirty(false);
            cancel();
        }
    };

    const cancel = () => {
        setTasksMetadata(getTasksMetadata(project.tasks));
    };

    const getNewLabels = useCallback(() => {
        const allLabels = tasksMetadata.reduce(
            (labels: LabelTreeLabelProps[], task) => [...labels, ...getFlattenedLabels(task.labels)],
            []
        );

        return allLabels.filter(isNew);
    }, [tasksMetadata]);

    const newLabels = getNewLabels();

    const saveHandler = () => {
        if (!isEmpty(newLabels)) {
            setDialogOpen(true);
        } else {
            save();
        }
    };

    const save = (shouldRevisit = false) => {
        editProjectLabelsMutation.mutate(
            {
                datasetIdentifier,
                project,
                tasksMetadata,
                shouldRevisit,
            },
            {
                onSettled: reload,
                onSuccess: () => {
                    const message = `Labels have been changed successfully.${
                        shouldRevisit ? ' All affected images are assigned the Revisit status. ' : ''
                    }`;

                    addNotification({ message, type: NOTIFICATION_TYPE.INFO });
                    setIsDirty(false);
                    setEditionEnablement(false);
                },
            }
        );
    };

    const revisitHandler = (shouldRevisit: boolean) => save(shouldRevisit);

    const editLabels = (labels: LabelTreeItem[], domain: DOMAIN) => {
        setTasksMetadata(
            tasksMetadata.map((task) => {
                if (domain === task.domain) {
                    return { ...task, labels };
                }

                return task;
            })
        );

        setIsDirty(true);
    };

    return (
        <>
            <PageLayout
                breadcrumbs={[{ id: 'labels-id', breadcrumb: 'Labels' }]}
                header={
                    <Flex gap={'size-100'} justifyContent={'end'}>
                        <TooltipTrigger placement={'bottom'}>
                            <Button onPress={editToggle} variant={'primary'}>
                                {isEditionEnabled ? 'Cancel editing' : 'Edit labels'}
                            </Button>
                            <Tooltip>{`${isEditionEnabled ? 'Turn off edit mode' : 'Turn on edit mode'}`}</Tooltip>
                        </TooltipTrigger>

                        {isEditionEnabled && isDirty && (
                            <>
                                <TooltipTrigger placement={'bottom'}>
                                    <Button onPress={saveHandler} variant={'accent'} isDisabled={!labelsValid}>
                                        Save
                                    </Button>
                                    <Tooltip>Save changes in project labels</Tooltip>
                                </TooltipTrigger>

                                <DialogContainer onDismiss={() => setDialogOpen(false)}>
                                    {isDialogOpen && (
                                        <RevisitAlertDialog flattenNewLabels={newLabels} save={revisitHandler} />
                                    )}
                                </DialogContainer>
                            </>
                        )}
                    </Flex>
                }
            >
                {editProjectLabelsMutation.isPending ? (
                    <Loading />
                ) : (
                    <>
                        {tasksMetadata.map((task, index) => (
                            <Fragment key={`${task.domain}-${index}`}>
                                {isTaskChainProject && !!index && <Divider size={'S'} marginY={'size-200'} />}
                                <ProjectTaskLabels
                                    task={task}
                                    isTaskChainProject={isTaskChainProject}
                                    isInEdition={isEditionEnabled}
                                    editLabels={editLabels}
                                    parentLabel={
                                        !!index ? getFlattenedLabels(tasksMetadata[index - 1].labels)[0] : undefined
                                    }
                                    setLabelsValidity={setLabelsValidity}
                                />
                            </Fragment>
                        ))}
                    </>
                )}
            </PageLayout>
            <UnsavedChangesDialog open={isOpen} setOpen={setIsOpen} onPrimaryAction={onUnsavedAction} />
        </>
    );
};
