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

import { Cell, Text } from '@adobe/react-spectrum';
import isNil from 'lodash/isNil';

import { OptimizedModel, TrainedModel } from '../../../../../../core/models/optimized-models.interface';
import { useApplicationServices } from '../../../../../../core/services/application-services-provider.component';
import { useModelIdentifier } from '../../../../../../hooks/use-model-identifier/use-model-identifier.hook';
import { ThreeDotsFlashing } from '../../../../../../shared/components/three-dots-flashing/three-dots-flashing.component';
import { useFormatModelAccuracy } from '../../../../../../shared/hooks/use-format-model-accuracy.hook';
import { PreselectedModel } from '../../../../project-details.interface';
import { TESTS_OPTIMIZATION_TYPES } from '../../../../utils';
import { ModelTableNameCell } from '../model-table/model-table-name-cell.component';
import { ModelTableColumns } from '../model-table/model-table.interface';
import { ModelVariantsMenuActions } from '../model-variants-menu-actions.component';
import { isOptimizedModel, isOptimizedModelNoReady, ModelTableColumnKeys } from '../utils';

interface useColumnsModelProps {
    taskId: string;
    version: number;
    hideMenu?: boolean;
    groupName: string;
    modelTemplateName: string;
    setSelectedModel: (value: PreselectedModel | undefined) => void;
}

const AccuracyCell = ({ accuracy }: { accuracy: number }): JSX.Element => {
    return <>{useFormatModelAccuracy(accuracy)}</>;
};

export const useColumnsModel = ({
    taskId,
    version,
    groupName,
    hideMenu = false,
    modelTemplateName,
    setSelectedModel,
}: useColumnsModelProps): ((
    firstColumnName: string,
    defaultDescription?: string
) => ModelTableColumns<OptimizedModel | TrainedModel>[]) => {
    const { router } = useApplicationServices();
    const modelIdentifier = useModelIdentifier();

    return (firstColumnName: string, defaultDescription = '') => [
        {
            label: firstColumnName,
            align: 'start',
            width: '1fr',
            component: (row) => {
                return (
                    <Cell key={`${row.id}-${ModelTableColumnKeys.MODEL_NAME}`}>
                        <ModelTableNameCell row={row} defaultDescription={defaultDescription} />
                    </Cell>
                );
            },
        },
        {
            label: 'LICENSE',
            width: 118,
            component: (row) => {
                return (
                    <Cell key={`${row.id}-${ModelTableColumnKeys.LICENSE}`}>
                        <Text id={`${row.id}-license`}>{row.license}</Text>
                    </Cell>
                );
            },
        },
        {
            label: 'PRECISION',
            width: 118,
            component: (row) => {
                const precision = Array.isArray(row.precision) ? row.precision.at(0) : row.precision;

                return (
                    <Cell key={`${row.id}-${ModelTableColumnKeys.PRECISION}`}>
                        <Text id={`${row.id}-precision`}>
                            {precision === undefined ? (
                                isOptimizedModelNoReady(row) ? (
                                    <ThreeDotsFlashing />
                                ) : undefined
                            ) : (
                                precision
                            )}
                        </Text>
                    </Cell>
                );
            },
        },
        {
            label: 'SCORE',
            width: 118,
            component: (row) => {
                if (isNil(row.accuracy)) {
                    return (
                        <Cell key={`${row.id}-${ModelTableColumnKeys.ACCURACY}`}>
                            <></>
                        </Cell>
                    );
                }

                return (
                    <Cell key={`${row.id}-${ModelTableColumnKeys.ACCURACY}`}>
                        <Text id={`${row.id}-accuracy`}>
                            {isOptimizedModelNoReady(row) ? (
                                <ThreeDotsFlashing />
                            ) : (
                                <AccuracyCell accuracy={row.accuracy} />
                            )}
                        </Text>
                    </Cell>
                );
            },
        },
        {
            label: 'SIZE',
            width: 100,
            component: (row) => {
                return (
                    <Cell key={`${row.id}-${ModelTableColumnKeys.MODEL_SIZE}`}>
                        <Text id={`${row.id}-modelSize`}>{row[ModelTableColumnKeys.MODEL_SIZE]}</Text>
                    </Cell>
                );
            },
        },
        {
            label: '',
            width: 100,
            component: (row) => {
                const key = isOptimizedModel(row) ? row.optimizationType : 'BASE';
                const preselectedOptimization = TESTS_OPTIMIZATION_TYPES[key];
                const downloadUrl = isOptimizedModel(row)
                    ? router.EXPORT_OPTIMIZED_MODEL(modelIdentifier, row.id)
                    : router.EXPORT_MODEL(modelIdentifier);

                if (isOptimizedModelNoReady(row) || hideMenu) {
                    return (
                        <Cell key={`${row.id}-${ModelTableColumnKeys.MENU}`}>
                            <></>
                        </Cell>
                    );
                }

                return (
                    <Cell key={`${row.id}-${ModelTableColumnKeys.MENU}`}>
                        <ModelVariantsMenuActions
                            modelId={row.id}
                            downloadUrl={downloadUrl}
                            handleOpenRunTest={() =>
                                setSelectedModel({
                                    groupId: modelIdentifier.groupId,
                                    groupName,
                                    id: modelIdentifier.modelId,
                                    taskId,
                                    version,
                                    optimizedModel: { ...preselectedOptimization, id: row.id },
                                    templateName: modelTemplateName,
                                })
                            }
                        />
                    </Cell>
                );
            },
        },
    ];
};
