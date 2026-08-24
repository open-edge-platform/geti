// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { useState } from 'react';

import { ActionButton } from '@geti-ui/ui';
import { Tag } from '@geti-ui/ui/icons';
import { useProject } from 'hooks/api/project.hook';
import { isEmpty } from 'lodash-es';

import { isClassificationTask } from '../../../project/task-type-guards';
import { BulkSelectedMediaLabelsAssignmentDialog } from '../bulk-labels-assignment/bulk-selected-media-labels-assignment-dialog.component';

type AssignLabelProps = {
    selectedImagesIds: string[];
};

export const AssignLabel = ({ selectedImagesIds }: AssignLabelProps) => {
    const { data: project } = useProject();
    const isClassification = isClassificationTask(project.task.task_type);
    const [isVisible, setIsVisible] = useState<boolean>(false);

    if (isClassification && !isEmpty(selectedImagesIds)) {
        return (
            <>
                <ActionButton margin={0} isQuiet onPress={() => setIsVisible(true)} aria-label={'Assign label'}>
                    <Tag />
                </ActionButton>
                <BulkSelectedMediaLabelsAssignmentDialog
                    isVisible={isVisible}
                    selectedImagesIds={selectedImagesIds}
                    onClose={() => setIsVisible(false)}
                />
            </>
        );
    }

    return null;
};
