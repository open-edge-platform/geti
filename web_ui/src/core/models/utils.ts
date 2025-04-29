// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { SortDirection } from '../../shared/components/table/table.interface';
import { ModelGroupsAlgorithmDetails, ModelsGroups, ModelVersion } from './models.interface';

export const isActiveModel = (model: ModelVersion) => model.isActiveModel;
const hasActiveVersions = (modelVersions: ModelVersion[]) => modelVersions.some(isActiveModel);
export const hasActiveModels = (modelsData: ModelsGroups) => hasActiveVersions(modelsData.modelVersions);

const sortByCreationDate = (
    modelA: Pick<ModelVersion, 'creationDate'>,
    modelB: Pick<ModelVersion, 'creationDate'>,
    sortDirection: SortDirection
) => {
    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;

    return modelA.creationDate.localeCompare(modelB.creationDate) * comparisonWeight;
};

export const sortModelsByCreationTime = (
    modelVersions: ModelVersion[],
    sortDirection: SortDirection
): ModelVersion[] => {
    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;

    return modelVersions.toSorted((modelA, modelB) => {
        return modelA.creationDate.localeCompare(modelB.creationDate) * comparisonWeight;
    });
};

export const sortModelsGroupsByCreationTime = (
    modelsGroups: ModelGroupsAlgorithmDetails[],
    sortDirection: SortDirection
): ModelGroupsAlgorithmDetails[] => {
    const sortModelsInsideGroup: ModelGroupsAlgorithmDetails[] = modelsGroups.map((modelGroup) => ({
        ...modelGroup,
        modelVersions: sortModelsByCreationTime(modelGroup.modelVersions, sortDirection),
    }));

    return sortModelsInsideGroup.toSorted((modelGroupA, modelGroupB) => {
        if (modelGroupA.taskId !== modelGroupB.taskId) {
            return 0;
        }

        const modelA = modelGroupA.modelVersions[0];
        const modelB = modelGroupB.modelVersions[0];

        return sortByCreationDate(modelA, modelB, sortDirection);
    });
};

export const sortModelsGroupsByActiveModel = (
    modelGroups: ModelGroupsAlgorithmDetails[],
    sortDirection: SortDirection
): ModelGroupsAlgorithmDetails[] => {
    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;
    return modelGroups.toSorted((modelGroupA, modelGroupB) => {
        if (modelGroupA.taskId === modelGroupB.taskId) {
            const hasModelGroupAActiveModel = modelGroupA.modelVersions.some(isActiveModel);

            if (hasModelGroupAActiveModel) {
                return -1 * comparisonWeight;
            }

            const hasModelGroupBActiveModel = modelGroupB.modelVersions.some(isActiveModel);

            if (hasModelGroupBActiveModel) {
                return 1 * comparisonWeight;
            }
        }

        return 0;
    });
};

const getScore = (model: ModelVersion): number => {
    return (
        (model.performance.type === 'default_performance' ? model.performance.score : model.performance.globalScore) ??
        0
    );
};

const sortModelsByScore = (models: ModelVersion[], sortDirection: SortDirection): ModelVersion[] => {
    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;

    return models.toSorted((modelA, modelB) => {
        const modelAScore = getScore(modelA);
        const modelBScore = getScore(modelB);

        return (modelAScore - modelBScore) * comparisonWeight;
    });
};

export const sortModelsGroupsByScore = (modelGroups: ModelGroupsAlgorithmDetails[], sortDirection: SortDirection) => {
    const sortModelsInsideGroup = modelGroups.map((modelGroup) => ({
        ...modelGroup,
        modelVersions: sortModelsByScore(modelGroup.modelVersions, sortDirection),
    }));

    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;

    return sortModelsInsideGroup.toSorted((modelGroupA, modelGroupB) => {
        if (modelGroupA.taskId !== modelGroupB.taskId) {
            return 0;
        }

        const modelScoreA = getScore(modelGroupA.modelVersions[0]);
        const modelScoreB = getScore(modelGroupB.modelVersions[0]);

        return (modelScoreA - modelScoreB) * comparisonWeight;
    });
};

export const sortModelsGroupsByComplexity = (
    modelsGroups: ModelGroupsAlgorithmDetails[],
    sortDirection: SortDirection
): ModelGroupsAlgorithmDetails[] => {
    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;

    return modelsGroups.toSorted((modelGroupA, modelGroupB) => {
        if (modelGroupA.taskId !== modelGroupB.taskId) {
            return 0;
        }

        const modelAComplexity = modelGroupA.complexity ?? 0;
        const modelBComplexity = modelGroupB.complexity ?? 0;

        return (modelAComplexity - modelBComplexity) * comparisonWeight;
    });
};

const sortModelsBySize = (models: ModelVersion[], sortDirection: SortDirection): ModelVersion[] => {
    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;

    return models.toSorted((modelA, modelB) => {
        const modelAWeightSize = modelA.modelSize;
        const modelBWeightSize = modelB.modelSize;

        return (modelAWeightSize - modelBWeightSize) * comparisonWeight;
    });
};

export const sortModelsGroupsByModelSize = (
    modelsGroups: ModelGroupsAlgorithmDetails[],
    sortDirection: SortDirection
): ModelGroupsAlgorithmDetails[] => {
    const sortModelsInsideGroup: ModelGroupsAlgorithmDetails[] = modelsGroups.map((modelGroup) => ({
        ...modelGroup,
        modelVersions: sortModelsBySize(modelGroup.modelVersions, sortDirection),
    }));

    const comparisonWeight = sortDirection === 'ASC' ? 1 : -1;

    return sortModelsInsideGroup.toSorted((modelGroupA, modelGroupB) => {
        if (modelGroupA.taskId !== modelGroupB.taskId) {
            return 0;
        }

        const modelASize = modelGroupA.modelVersions[0].modelSize;
        const modelBSize = modelGroupB.modelVersions[0].modelSize;

        return (modelASize - modelBSize) * comparisonWeight;
    });
};
