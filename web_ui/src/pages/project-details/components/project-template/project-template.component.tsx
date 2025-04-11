// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { ButtonGroup, View } from '@adobe/react-spectrum';
import { v4 as uuidv4 } from 'uuid';

import { InfoOutline } from '../../../../assets/icons';
import { KeypointNode } from '../../../../core/annotations/shapes.interface';
import { Label } from '../../../../core/labels/label.interface';
import { useProjectActions } from '../../../../core/projects/hooks/use-project-actions.hook';
import { KeypointTask, Task, TaskMetadata } from '../../../../core/projects/task.interface';
import { isKeypointTask } from '../../../../core/projects/utils';
import { useHistoryBlock } from '../../../../hooks/use-history-block/use-history-block.hook';
import { NOTIFICATION_TYPE } from '../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../notification/notification.component';
import { useWorkspaceIdentifier } from '../../../../providers/workspaces-provider/use-workspace-identifier.hook';
import { Button } from '../../../../shared/components/button/button.component';
import { PageLayout } from '../../../../shared/components/page-layout/page-layout.component';
import { UnsavedChangesDialog } from '../../../../shared/components/unsaved-changes-dialog/unsaved-changes-dialog.component';
import { isNonEmptyString } from '../../../../shared/utils';
import { InfoSection } from '../../../create-project/components/info-section/info-section.component';
import { TemplateManager } from '../../../create-project/components/pose-template/template-manager.component';
import {
    EdgeLine,
    getProjectTypeMetadata,
    getValidationError,
    TemplateState,
} from '../../../create-project/components/pose-template/util';
import { useProject } from '../../providers/project-provider/project-provider.component';

const hasEqualLabelId = (id: string) => (point: KeypointNode) => point.label.id === id;

const getInitialKeypointStructure = ({ keypointStructure: { edges, positions } }: KeypointTask): TemplateState => {
    const linkedEdged = edges.map(({ nodes: [fromId, toId] }) => {
        const toLabel = positions.find(hasEqualLabelId(fromId));
        const fromLabel = positions.find(hasEqualLabelId(toId));

        return { id: uuidv4(), from: toLabel, to: fromLabel } as EdgeLine;
    });

    return { edges: linkedEdged, points: positions };
};

const formatWithTaskMetadata = (metadata: TaskMetadata | null) => (task: KeypointTask | Task) => {
    if (metadata && isKeypointTask(task)) {
        return { ...task, keypointStructure: metadata.keypointStructure, labels: metadata.labels as Label[] };
    }

    return task;
};

export const ProjectTemplate = (): JSX.Element => {
    const { project } = useProject();
    const { addNotification } = useNotification();
    const [isDirty, setIsDirty] = useState(false);
    const { editProjectMutation } = useProjectActions();
    const [taskMetadata, setTaskMetadata] = useState<TaskMetadata | null>(null);
    const { organizationId, workspaceId } = useWorkspaceIdentifier();
    const [isOpen, setIsOpen, onUnsavedAction] = useHistoryBlock(isDirty);

    const keypointTask = project.tasks.find(isKeypointTask);
    const initialKeypointStructure = keypointTask
        ? getInitialKeypointStructure(keypointTask)
        : { edges: [], points: [] };

    const [keypointStructure, setKeypointStructure] = useState(initialKeypointStructure);

    const errors = getValidationError(keypointStructure.points);

    const handleSave = () => {
        editProjectMutation.mutate(
            {
                projectIdentifier: { organizationId, workspaceId, projectId: project.id },
                project: { ...project, tasks: project.tasks.map(formatWithTaskMetadata(taskMetadata)) },
            },
            {
                onSuccess: () => {
                    setIsDirty(false);
                    addNotification({
                        type: NOTIFICATION_TYPE.INFO,
                        message: 'Template have been updated successfully',
                    });
                },
            }
        );
    };

    return (
        <>
            <PageLayout breadcrumbs={[{ id: 'labels-id', breadcrumb: 'Template' }]}>
                <View backgroundColor={'gray-75'} padding={'size-300'} height={'100%'}>
                    <TemplateManager
                        gap={'size-300'}
                        isAddPointEnabled={false}
                        isTemplatesVisible={false}
                        isLabelOptionsEnabled={false}
                        initialNormalizedState={initialKeypointStructure}
                        onTemplateChange={({ roi, ...newStructure }) => {
                            setIsDirty(true);
                            setKeypointStructure(newStructure);
                            setTaskMetadata(getProjectTypeMetadata(newStructure.points, newStructure.edges, roi));
                        }}
                    >
                        {isNonEmptyString(errors) ? (
                            <InfoSection icon={<InfoOutline />} message={errors} marginTop={0} height={'size-400'} />
                        ) : (
                            <ButtonGroup align='end'>
                                <Button
                                    onPress={handleSave}
                                    isDisabled={!isDirty}
                                    isPending={editProjectMutation.isPending}
                                >
                                    Update Template
                                </Button>
                            </ButtonGroup>
                        )}
                    </TemplateManager>
                </View>
            </PageLayout>
            <UnsavedChangesDialog open={isOpen} setOpen={setIsOpen} onPrimaryAction={onUnsavedAction} />
        </>
    );
};
