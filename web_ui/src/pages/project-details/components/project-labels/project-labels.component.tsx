// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Fragment, useCallback, useEffect, useState } from 'react';

import { DialogContainer, Divider, Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Button, Loading } from '@geti/ui';
import { isEmpty } from 'lodash-es';

import {
    LabelItemEditionState,
    LabelTreeItem,
    LabelTreeLabelProps,
} from '../../../../core/labels/label-tree-view.interface';
import { getFlattenedItems, getFlattenedLabels, getNonEmptyLabelsFromProject } from '../../../../core/labels/utils';
import { DOMAIN } from '../../../../core/projects/core.interface';
import { isClassificationDomain } from '../../../../core/projects/domains';
import { useProjectActions } from '../../../../core/projects/hooks/use-project-actions.hook';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { useHistoryBlock } from '../../../../hooks/use-history-block/use-history-block.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { isNew } from '../../../../shared/components/label-tree-view/label-tree-view-item/utils';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
import { UnsavedChangesDialog } from '../../../../shared/components/unsaved-changes-dialog/unsaved-changes-dialog.component';
import { pluralize } from '../../../../shared/utils';
import { useDatasetIdentifier } from '../../../annotator/hooks/use-dataset-identifier.hook';
import { useProject } from '../../providers/project-provider/project-provider.component';
import { ProjectTaskLabels } from './project-task-labels/project-task-labels.component';
import { RevisitAlertDialog } from './revisit-alert-dialog/revisit-alert-dialog.component';
import { getTasksMetadata } from './utils';

export const ProjectLabels = (): JSX.Element => {
    const { editProjectLabelsMutation } = useProjectActions();
    const datasetIdentifier = useDatasetIdentifier();

    const { project, isTaskChainProject, reload, isSingleDomainProject } = useProject();

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

    const hasMinimumNumberOfLabels = (): boolean => {
        const labelsToBeRemoved = getFlattenedItems(tasksMetadata.flatMap((task) => task.labels)).filter(
            (label) => label.state === LabelItemEditionState.REMOVED
        );

        if (labelsToBeRemoved.length === 0) {
            return true;
        }

        const projectLabels = getNonEmptyLabelsFromProject(project.tasks);
        const minimumNeededLabels = isSingleDomainProject(isClassificationDomain) ? 2 : 1;

        if (projectLabels.length - labelsToBeRemoved.length < minimumNeededLabels) {
            addNotification({
                message: `You must have at least ${pluralize(minimumNeededLabels, 'label')} in the project.`,
                type: NOTIFICATION_TYPE.INFO,
                dismiss: { duration: 0 },
            });

            return false;
        }

        return true;
    };

    const saveButtonDisabled = !labelsValid || !hasMinimumNumberOfLabels();

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
                                    <Button onPress={saveHandler} variant={'accent'} isDisabled={saveButtonDisabled}>
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
