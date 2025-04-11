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

import { FC } from 'react';

import isEmpty from 'lodash/isEmpty';

import { OptimizedModel } from '../../../../../../core/models/optimized-models.interface';
import { PreselectedModel } from '../../../../project-details.interface';
import { RunTestDialog } from '../../../project-tests/run-test-dialog/run-test-dialog.component';
import { ModelTable } from '../model-table/model-table.component';

// applies selected-tab icon opacity
import './../model-variants.module.scss';

import { isBaselineModel, isNotBaselineModel } from './uitls';
import { useColumnsModel } from './use-columns-model.hook';

interface OptimizedModelTabProps {
    areOptimizedModelsVisible: boolean;
    hasBaselineModels?: boolean;
    emptyModelMessage?: string;
    models: OptimizedModel[];
    columns: ReturnType<typeof useColumnsModel>;
    selectedModel: PreselectedModel | undefined;
    setSelectedModel: (value: PreselectedModel | undefined) => void;
}

export const OptimizedModelTab: FC<OptimizedModelTabProps> = ({
    hasBaselineModels = true,
    emptyModelMessage = '',
    areOptimizedModelsVisible,
    models,
    columns,
    selectedModel,
    setSelectedModel,
}: OptimizedModelTabProps): JSX.Element => {
    const baselineModelsData = !hasBaselineModels ? [] : models.filter(isBaselineModel);
    const optimizedModelsData = !hasBaselineModels ? models : models.filter(isNotBaselineModel);

    const hasEmptyModels = isEmpty(baselineModelsData) && isEmpty(optimizedModelsData);

    return (
        <>
            <ModelTable marginTop={'size-200'} data={baselineModelsData} columns={columns('BASELINE MODELS')} />

            <ModelTable
                data={areOptimizedModelsVisible ? optimizedModelsData : []}
                marginTop={isEmpty(baselineModelsData) ? 'size-200' : 'size-300'}
                emptyModelMessage={hasEmptyModels ? emptyModelMessage : ''}
                columns={columns('OPTIMIZED MODELS')}
            />

            <RunTestDialog
                isOpen={Boolean(selectedModel)}
                handleClose={() => setSelectedModel(undefined)}
                preselectedModel={selectedModel}
            />
        </>
    );
};
