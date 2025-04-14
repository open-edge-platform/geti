// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Cell } from '@adobe/react-spectrum';
import { QueryObserverResult } from '@tanstack/react-query';

import { OptimizedModel, TrainedModel } from '../../../../../../core/models/optimized-models.interface';
import { LifecycleStage } from '../../../../../../core/supported-algorithms/dtos/supported-algorithms.interface';
import { PreselectedModel } from '../../../../project-details.interface';
import { ModelTableColumns } from '../model-table/model-table.interface';
import { StartOptimization } from '../optimization/start-optimization/start-optimization.component';
import { useIsModelBeingOptimized } from '../use-is-model-being-optimized.hook';
import { isOptimizedModelNoReady, ModelTableColumnKeys } from '../utils';
import { useColumnsModel } from './use-columns-model.hook';

interface UseOpenVinoColumnsProps {
    taskId: string;
    isModelDeleted: boolean;
    modelTemplateName: string;
    groupName: string;
    version: number;
    hasStartOptimizationButton: boolean;
    setSelectedModel: (value: PreselectedModel | undefined) => void;
    refetchModels: () => Promise<QueryObserverResult>;
}

export const useOpenVinoColumns = ({
    taskId,
    hasStartOptimizationButton,
    setSelectedModel,
    isModelDeleted,
    modelTemplateName,
    groupName,
    version,
}: UseOpenVinoColumnsProps): ReturnType<typeof useColumnsModel> => {
    const isModelBeingOptimized = useIsModelBeingOptimized(hasStartOptimizationButton);

    const columns = useColumnsModel({
        taskId,
        version,
        groupName,
        modelTemplateName,
        setSelectedModel,
        hideMenu: isModelDeleted,
    });

    const disabledTooltip =
        `The algorithm version used for training this model is obsolete, so this model` +
        ` cannot be optimized. Please retrain a new model first.`;

    if (hasStartOptimizationButton) {
        return (firstColumnName: string, defaultDescription = '') => {
            const localColumns = columns(firstColumnName, defaultDescription);
            const columnsWithoutLastOne = localColumns.slice(0, -1);
            const lastColumn = localColumns[localColumns.length - 1];

            const columnWithStartOptimizationButton: ModelTableColumns<OptimizedModel | TrainedModel> = {
                label: '',
                align: 'end',
                width: 200,
                component: (model) => {
                    if (isOptimizedModelNoReady(model)) {
                        return (
                            <Cell key={`${model.id}-${ModelTableColumnKeys.MENU}`}>
                                <StartOptimization
                                    isModelBeingOptimized={Boolean(isModelBeingOptimized)}
                                    isDisabled={model.lifecycleStage === LifecycleStage.OBSOLETE}
                                    disabledTooltip={disabledTooltip}
                                />
                            </Cell>
                        );
                    }

                    return lastColumn.component(model);
                },
            };

            return [...columnsWithoutLastOne, columnWithStartOptimizationButton];
        };
    }

    return columns;
};
