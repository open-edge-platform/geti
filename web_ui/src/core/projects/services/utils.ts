// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { differenceBy, omit } from 'lodash-es';

import { API_URLS } from '../../../../packages/core/src/services/urls';
import { hasEqualId } from '../../../shared/utils';
import { fetchLabelsTree } from '../../labels/annotator-utils/labels-utils';
import {
    DeletedLabelDTO,
    EditedLabelDTO,
    LabelCreation,
    LabelDTO,
    NewLabelDTO,
    RevisitLabelDTO,
} from '../../labels/dtos/label.interface';
import { LabelItemType, LabelTreeItem, LabelTreeLabelProps } from '../../labels/label-tree-view.interface';
import {
    DeletedLabel,
    EditedLabel,
    Label,
    LABEL_BEHAVIOUR,
    LabelsRelationType,
    RevisitLabel,
} from '../../labels/label.interface';
import {
    filterOutEmptyAndBackgroundLabel,
    getBehaviourFromDTO,
    getFlattenedItems,
    getFlattenedLabels,
    GROUP_SEPARATOR,
    isAnomalous,
    isBackgroundLabel,
    isEmptyLabel,
} from '../../labels/utils';
import { DOMAIN } from '../core.interface';
import { Dataset } from '../dataset.interface';
import { isKeypointDetection } from '../domains';
import {
    ConnectionDTO,
    DatasetDTO,
    EditProjectDTO,
    PerformanceDTO,
    ProjectDTO,
    ScoreDTO,
} from '../dtos/project.interface';
import { ProjectStatusDTO } from '../dtos/status.interface';
import {
    CropTask,
    DatasetTask,
    KeypointStructureDTO,
    KeypointTaskCreation,
    KeypointTaskDTO,
    TASK_TYPE,
    TaskCreation,
    TaskDTO,
} from '../dtos/task.interface';
import { getDomain, ProjectProps } from '../project.interface';
import {
    EditTask,
    KeypointStructure,
    KeypointTask,
    Performance,
    PerformanceType,
    Score,
    Task,
    TaskMetadata,
} from '../task.interface';
import { getTaskTypeFromDomain, isKeypointTask } from '../utils';

const getRevisitLabel = (label: RevisitLabelDTO, domain: DOMAIN): RevisitLabel => {
    const { name, color, group, parent_id, hotkey, revisit_affected_annotations, id, is_empty } = label;
    const behaviour = getBehaviourFromDTO(label, domain);

    return {
        id,
        name,
        color,
        group,
        parentLabelId: parent_id || null,
        hotkey,
        behaviour,
        revisitAffectedAnnotations: revisit_affected_annotations,
        isEmpty: is_empty,
    };
};

// We need to transform labels from Model details service but
// it doesn't have access to the project domains to get the label's 'behaviour',
// and updating the current helpers/components to make them fit with a new interface is a lot of work.
// Keeping in mind that model-labels don't have any functionality but render the tree-view,
// this helper is a straightforward solution.
export const getRawNewLabel = (label: LabelDTO): Label => {
    const { id, name, color, group, parent_id, is_empty } = label;

    return {
        id,
        name,
        color,
        group,
        // We only care about it being exclusive or not
        behaviour: is_empty ? LABEL_BEHAVIOUR.EXCLUSIVE : LABEL_BEHAVIOUR.LOCAL,
        parentLabelId: parent_id || null,
        isEmpty: is_empty,
    };
};

const getDeletedLabel = (label: DeletedLabelDTO, domain: DOMAIN): DeletedLabel => {
    const { name, color, group, parent_id, hotkey, is_deleted, id, is_empty } = label;
    const behaviour = getBehaviourFromDTO(label, domain);

    return {
        id,
        name,
        color,
        group,
        parentLabelId: parent_id || null,
        hotkey,
        behaviour,
        isDeleted: is_deleted,
        isEmpty: is_empty,
    };
};

const getLabel = (label: LabelDTO, domain: DOMAIN): Label => {
    const { id, name, color, group, parent_id, hotkey, is_empty } = label;
    const behaviour = getBehaviourFromDTO(label, domain);

    return {
        id,
        name,
        color,
        group,
        parentLabelId: parent_id || null,
        hotkey,
        behaviour,
        isEmpty: is_empty,
    };
};

const getScore = (score: ScoreDTO | null | undefined): Score | null => {
    if (score == null) {
        return null;
    }

    const { value, metric_type } = score;

    return {
        value,
        metricType: metric_type,
    };
};

const getScoreDTO = (score: Score | null): ScoreDTO | null => {
    if (score == null) {
        return null;
    }

    const { value, metricType } = score;

    return {
        value,
        metric_type: metricType,
    };
};

export const getPerformance = (performanceDTO: PerformanceDTO, tasks: Task[] = []): Performance => {
    if (performanceDTO?.local_score !== undefined && performanceDTO.global_score !== undefined) {
        const { score, local_score, global_score, task_performances } = performanceDTO;

        return {
            score,
            type: PerformanceType.ANOMALY,
            globalScore: global_score,
            localScore: local_score,
            taskPerformances: task_performances.map((taskPerformance) => ({
                domain: tasks.find(({ id }) => id === taskPerformance.task_id)?.domain,
                taskNodeId: taskPerformance.task_id,
                score: getScore(taskPerformance.score),
                globalScore: getScore(taskPerformance.global_score),
                localScore: getScore(taskPerformance.local_score),
            })),
        };
    }

    const { score, task_performances } = performanceDTO;

    return {
        score,
        type: PerformanceType.DEFAULT,
        taskPerformances: task_performances.map((taskPerformance) => ({
            domain: tasks.find(({ id }) => id === taskPerformance.task_id)?.domain,
            taskNodeId: taskPerformance.task_id,
            score: getScore(taskPerformance.score),
        })),
    };
};

const getPerformanceDTO = (performance: Performance): PerformanceDTO => {
    if (performance.type === PerformanceType.ANOMALY) {
        const { score, taskPerformances, globalScore, localScore } = performance;

        return {
            score,
            global_score: globalScore,
            local_score: localScore,
            task_performances: taskPerformances.map((taskPerformance) => ({
                task_id: taskPerformance.taskNodeId,
                score: getScoreDTO(taskPerformance.score),
                global_score: getScoreDTO(taskPerformance.globalScore),
                local_score: getScoreDTO(taskPerformance.localScore),
            })),
        };
    }

    const { score, taskPerformances } = performance;

    return {
        score,
        task_performances: taskPerformances.map((taskPerformance) => ({
            task_id: taskPerformance.taskNodeId,
            score: getScoreDTO(taskPerformance.score),
        })),
    };
};

const getCommonTaskStructure = (task: TaskDTO, domain: DOMAIN) => {
    const labels = (task.labels ?? []).map((label) => {
        if ('revisit_affected_annotations' in label) {
            /** NOTE: We got labels from the server, there will be no new ones */
            return getRevisitLabel(label as RevisitLabelDTO, domain);
        }
        if ('is_deleted' in label) {
            return getDeletedLabel(label, domain);
        }

        return getLabel(label, domain);
    });

    // NOTE: creation of tree transform Label to LabelTreeViewLabel, we have to translate to Label again
    const labelsSortedByStructure: LabelTreeLabelProps[] = getFlattenedLabels(
        fetchLabelsTree(filterOutEmptyAndBackgroundLabel(labels))
    );

    const commonStructure = {
        id: task.id,
        title: task.title,
        domain,
        labels: [...labelsSortedByStructure, ...getEmptyAndBackgroundLabels(labels)],
    };

    return commonStructure;
};

const getEmptyAndBackgroundLabels = (labels: Label[]) => {
    const emptyLabel = labels.find(isEmptyLabel);
    const backgroundLabel = labels.find(isBackgroundLabel);

    if (emptyLabel && backgroundLabel) {
        return [emptyLabel, backgroundLabel];
    }

    if (backgroundLabel) {
        return [backgroundLabel];
    }

    if (emptyLabel) {
        return [emptyLabel];
    }

    return [];
};

const isKeypointType = (otherTask: TaskDTO | KeypointTaskDTO): otherTask is KeypointTaskDTO => {
    const domain = getDomain(otherTask.task_type);
    return domain !== undefined && isKeypointDetection(domain);
};

const getKeypointStructure = (structureDTO: KeypointStructureDTO, labels: Label[]): KeypointStructure => {
    return {
        ...structureDTO,
        positions: structureDTO.positions.map((position) => {
            const [label] = labels.filter(hasEqualId(position.label));

            return { label, edgeEnds: [], isVisible: true, x: position.x, y: position.y, isSelected: false };
        }),
    };
};

export const getProjectEntity = (serverProject: ProjectDTO, router = API_URLS): ProjectProps => {
    const {
        id,
        name,
        creation_time,
        thumbnail,
        datasets: datasetsDTO = [],
        performance: performanceDTO,
        storage_info,
        pipeline: { tasks },
    } = serverProject;

    const projectTasks = tasks
        .map((task): Task | EditTask | KeypointTask | undefined => {
            const domain = getDomain(task.task_type);

            if (domain === undefined) {
                return undefined;
            }

            const commonStructure = getCommonTaskStructure(task, domain);

            return isKeypointType(task)
                ? {
                      ...commonStructure,
                      keypointStructure: getKeypointStructure(task.keypoint_structure, commonStructure.labels),
                  }
                : commonStructure;
        })
        .filter((task): task is Task => task !== undefined);

    const labels = projectTasks.flatMap((task) => task.labels);
    const domains = projectTasks.map((task) => task.domain);
    const datasets = datasetsDTO.map(getDatasetEntity);

    const performance = getPerformance(performanceDTO, projectTasks);

    return {
        id,
        name,
        thumbnail: router.PREFIX(thumbnail),
        performance,
        tasks: projectTasks,
        creationDate: new Date(creation_time),
        domains,
        labels,
        datasets,
        storageInfo: storage_info ?? {},
    };
};

const getLabelDTO = (label: EditedLabel): EditedLabelDTO => {
    const { name, color, group, parentLabelId, hotkey, isEmpty, behaviour } = label;

    const common = {
        name,
        color,
        group,
        hotkey,
        parent_id: parentLabelId,
        is_empty: isEmpty,
        is_background: behaviour === LABEL_BEHAVIOUR.BACKGROUND,
        is_anomalous: isAnomalous(label),
    };

    if ('revisitAffectedAnnotations' in label) {
        if ('id' in label) {
            return {
                ...common,
                id: label.id,
                revisit_affected_annotations: label.revisitAffectedAnnotations,
            } as RevisitLabelDTO;
        }
        return {
            ...common,
            revisit_affected_annotations: label.revisitAffectedAnnotations,
        } as NewLabelDTO;
    } else if ('isDeleted' in label) {
        return {
            ...common,
            id: label.id,
            is_deleted: label.isDeleted,
        } as DeletedLabelDTO;
    } else {
        return {
            id: label.id,
            ...common,
        } as LabelDTO;
    }
};

const updateToTaskDTO = (task: Task, anomalyRevampFlagEnabled: boolean) => {
    return {
        id: task.id,
        task_type: getTaskTypeFromDomain(task.domain, anomalyRevampFlagEnabled),
        title: task.title,
        labels: task.labels.map(getLabelDTO),
    };
};

const updateToKeypointTaskDTO = (task: KeypointTask, anomalyRevampFlagEnabled: boolean) => {
    return {
        ...updateToTaskDTO(task, anomalyRevampFlagEnabled),
        keypoint_structure: {
            ...task.keypointStructure,
            positions: task.keypointStructure.positions.map((position) => ({ ...position, label: position.label.id })),
        },
    };
};

export const getEditProjectDTO = (
    project: ProjectProps,
    prevTasks: TaskDTO[] = [],
    anomalyRevampFlagEnabled = false
) => {
    const { id, name, creationDate, thumbnail, datasets, tasks, performance } = project;

    const tasksDTO = tasks.map((task): TaskDTO | KeypointTaskDTO => {
        if (isKeypointTask(task)) {
            return updateToKeypointTaskDTO(task, anomalyRevampFlagEnabled);
        }

        return updateToTaskDTO(task, anomalyRevampFlagEnabled);
    });

    // TODO UI: Remove 'keypoint_structure' from non-keypoint tasks.
    // Once it is removed from the response, the 'omit' line can be deleted.
    const missingTasksDTO = differenceBy(prevTasks, tasksDTO, 'id').map((task) => omit(task, 'keypoint_structure'));

    const allTasksDTO = [...missingTasksDTO, ...tasksDTO];

    const editedProjectBase: EditProjectDTO = {
        creation_time: creationDate.toUTCString(),
        id,
        name,
        pipeline: {
            connections: getConnectionsByTaskId(allTasksDTO),
            tasks: allTasksDTO,
        },
        performance: getPerformanceDTO(performance),
        thumbnail,
        datasets: datasets.map(getDatasetDTO),
    };

    return editedProjectBase;
};

const getDatasetLinkedTask = (datasetIdentifier: string, taskIdentifier: string) => [
    {
        from: datasetIdentifier,
        to: taskIdentifier,
    },
];

const getConnectionsByTaskId = (tasks: TaskDTO[]): ConnectionDTO[] => {
    return tasks
        .flatMap((task: TaskDTO, index) => (index ? [{ from: tasks[index - 1].id, to: task.id }] : undefined))
        .filter((task) => !!task) as ConnectionDTO[];
};

export const getConnectionsByTaskNames = (domains: DOMAIN[]): ConnectionDTO[] => {
    if (domains.length === 1) {
        const domain = domains[0];

        return getDatasetLinkedTask('Dataset', domain);
    }

    return domains.flatMap((domain: DOMAIN, index) => {
        if (index === 0) {
            return getDatasetLinkedTask('Dataset', domain);
        } else {
            return [
                { from: domains[index - 1], to: 'Crop' },
                { from: 'Crop', to: domain },
            ];
        }
    });
};

export const updateHierarchyParentId = (flatItems: LabelTreeItem[]): LabelTreeItem[] => {
    return flatItems.map((item) => {
        const parent = flatItems.find(hasEqualId(item.parentLabelId));

        if (parent?.type === LabelItemType.GROUP) {
            return { ...item, parentLabelId: parent.parentLabelId };
        }
        return item;
    });
};

const getPreparedLabels = (
    taskLabels: LabelTreeItem[],
    isMixedRelation: boolean,
    groupPrefix: string
): LabelCreation[] => {
    let flatItems = getFlattenedItems(taskLabels);
    if (isMixedRelation) {
        flatItems = updateHierarchyParentId(flatItems);
    }
    const flatLabels = flatItems.filter(({ type }) => type === LabelItemType.LABEL);

    return flatLabels.map((label: LabelTreeItem): LabelCreation => {
        const { name, color, group, hotkey, parentLabelId } = label as Label;

        const parentLabelElement = flatLabels.find(hasEqualId(parentLabelId));

        const groupName = `${groupPrefix}${group}`;

        return {
            name: name.trim(),
            color,
            group: groupName.trim(),
            parent_id: parentLabelElement ? parentLabelElement.name : null,
            hotkey,
        };
    });
};

const datasetTask: DatasetTask = {
    title: 'Dataset',
    task_type: TASK_TYPE.DATASET,
};

export const getPreparedTasks = (
    tasks: TaskMetadata[],
    domains: DOMAIN[],
    anomalyRevampFlagEnabled = false
): TaskCreation[] => {
    // TODO: in the future when we support task chains with more than 2 tasks,
    // we will need to generate a crop task in between each domain
    const cropTasks: CropTask[] = domains.length > 1 ? [{ title: 'Crop', task_type: TASK_TYPE.CROP }] : [];

    const preparedTasks = tasks.map((task, index): TaskCreation => {
        const groupPrefix = index === 1 ? `${(tasks[0].labels[0] as LabelTreeLabelProps).group}${GROUP_SEPARATOR}` : '';
        const labels = getPreparedLabels(task.labels, task.relation === LabelsRelationType.MIXED, groupPrefix);

        return {
            title: task.domain,
            task_type: getTaskTypeFromDomain(task.domain, anomalyRevampFlagEnabled),
            labels,
        };
    });
    const tasksDomains = tasks.map((task) => task.domain);
    const tasksWithoutLabels = domains
        .filter((domain) => {
            return !tasksDomains.includes(domain);
        })
        .map((domain) => {
            return {
                title: domain,
                task_type: getTaskTypeFromDomain(domain, anomalyRevampFlagEnabled),
            } as TaskCreation;
        });

    return [datasetTask, ...preparedTasks, ...tasksWithoutLabels, ...cropTasks];
};

export const getPreparedKeypointTasks = (tasks: TaskMetadata[], domains: DOMAIN[]): TaskCreation[] => {
    const cropTasks: CropTask[] = domains.length > 1 ? [{ title: 'Crop', task_type: TASK_TYPE.CROP }] : [];

    const preparedTasks = tasks.map((task): KeypointTaskCreation => {
        return {
            title: task.domain,
            task_type: TASK_TYPE.KEYPOINT_DETECTION,
            labels: getPreparedLabels(task.labels, false, 'keypoint-detection'),
            keypoint_structure: task?.keypointStructure ?? { edges: [], positions: [] },
        };
    });

    return [datasetTask, ...preparedTasks, ...cropTasks];
};

export const getProjectStatusBody = (time_remaining?: number, progress?: number): ProjectStatusDTO => {
    return {
        is_training: true,
        n_required_annotations: 0,
        project_performance: {
            score: 0.1,
            task_performances: [
                {
                    score: {
                        value: 0.1,
                        metric_type: 'accuracy',
                    },
                    task_id: 'task-id',
                },
            ],
        },
        tasks: [],
        status: {
            progress: progress || 4.132231404958678,
            time_remaining: time_remaining || 63,
        },
    };
};

export const getDatasetEntity = (dataset: DatasetDTO): Dataset => {
    const { id, name, use_for_training, creation_time } = dataset;

    return {
        id,
        name,
        useForTraining: use_for_training,
        creationTime: creation_time,
    };
};

const getDatasetDTO = (dataset: Dataset): DatasetDTO => {
    const { id, name, useForTraining, creationTime } = dataset;

    return {
        id,
        name,
        use_for_training: useForTraining,
        creation_time: creationTime,
    };
};
