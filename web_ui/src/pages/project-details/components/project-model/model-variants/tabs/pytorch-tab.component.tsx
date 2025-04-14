// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
