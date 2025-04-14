// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { UseQueryResult } from '@tanstack/react-query';
import isEmpty from 'lodash/isEmpty';

import { isNewState } from '../../../shared/components/label-tree-view/label-tree-view-item/utils';
import { ExportStatusStateDTO } from '../../configurable-parameters/dtos/configurable-parameters.interface';
import { JobProjectExportStatus } from '../../jobs/jobs.interface';
import { LabelItemEditionState, LabelTreeItem } from '../../labels/label-tree-view.interface';
import { EditedLabel, LabelsRelationType } from '../../labels/label.interface';
import {
    getDeletedLabelPayload,
    getFlattenedItems,
    getLabelPayload,
    getNewLabelPayloadNew,
    onlyLabelsFilter,
} from '../../labels/utils';
import { JobStateToExportStatus } from '../services/api-project-service';
import { updateHierarchyParentId } from '../services/utils';
import { EditTask, TaskMetadata } from '../task.interface';

export const getEditLabelsPayload = (
    labels: LabelTreeItem[],
    relation: LabelsRelationType,
    shouldRevisit = false
): EditedLabel[] => {
    let flatItems = getFlattenedItems(labels).filter(({ name }) => !isEmpty(name));

    if (relation === LabelsRelationType.MIXED) {
        flatItems = updateHierarchyParentId(flatItems);
    }

    const validLabels = flatItems.filter(onlyLabelsFilter);

    const labelsPayloads = validLabels.map((label): EditedLabel => {
        const { state, parentLabelId } = label;
        if (isNewState(state)) {
            const parentElement = validLabels.find(({ id }) => parentLabelId === id);

            if (parentElement === undefined) {
                return getNewLabelPayloadNew(label, shouldRevisit);
            }

            return getNewLabelPayloadNew({ ...label, parentLabelId: parentElement.name }, shouldRevisit);
        }

        if (state === LabelItemEditionState.REMOVED) {
            return getDeletedLabelPayload(label);
        }

        return getLabelPayload(label);
    });

    return labelsPayloads;
};

export const getEditTasksEntity = (projectTasks: EditTask[], tasksMetadata: TaskMetadata[], shouldRevisit: boolean) => {
    return projectTasks.map((task): EditTask => {
        const taskMetadata = tasksMetadata.find(({ domain }) => task.domain === domain);

        if (taskMetadata === undefined) {
            return task;
        }

        const { labels, relation } = taskMetadata;

        const labelsPayloads = getEditLabelsPayload(labels, relation, shouldRevisit);

        return { ...task, labels: labelsPayloads };
    });
};

export const isStateDone = (state?: ExportStatusStateDTO): boolean => state === ExportStatusStateDTO.DONE;
export const isStateError = (state?: ExportStatusStateDTO): boolean => state === ExportStatusStateDTO.ERROR;

export const isResponseErrorQuery = (query: UseQueryResult<JobProjectExportStatus, Error>) => {
    const state = query.data !== undefined ? JobStateToExportStatus[query.data?.state] : undefined;
    return isStateError(state) || query.isError;
};
