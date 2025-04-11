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

import { useState } from 'react';

import { ModelDetails } from '../../../../../../core/models/optimized-models.interface';
import { PreselectedModel } from '../../../../project-details.interface';
import { isModelDeleted } from '../../../../utils';
import { RunTestDialog } from '../../../project-tests/run-test-dialog/run-test-dialog.component';
import { ModelTable } from '../model-table/model-table.component';
import { useColumnsModel } from './use-columns-model.hook';

interface PytorchTabProps {
    taskId: string;
    version: number;
    groupName: string;
    modelTemplateName: string;
    modelDetails: ModelDetails;
}

export const PytorchTab = ({
    taskId,
    version,
    groupName,
    modelTemplateName,
    modelDetails,
}: PytorchTabProps): JSX.Element => {
    const [selectedModel, setSelectedModel] = useState<PreselectedModel | undefined>(undefined);

    const getModelColumns = useColumnsModel({
        taskId,
        version,
        groupName,
        modelTemplateName,
        setSelectedModel,
        hideMenu: isModelDeleted(modelDetails),
    });

    return (
        <>
            <ModelTable
                marginTop={'size-200'}
                data={[modelDetails.trainedModel]}
                columns={getModelColumns('BASELINE MODELS', 'Training model')}
            />

            <RunTestDialog
                isOpen={Boolean(selectedModel)}
                handleClose={() => setSelectedModel(undefined)}
                preselectedModel={selectedModel}
            />
        </>
    );
};
