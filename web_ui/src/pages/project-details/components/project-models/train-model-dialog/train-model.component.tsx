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

import isEmpty from 'lodash/isEmpty';

import { ModelGroupsAlgorithmDetails } from '../../../../../core/models/models.interface';
import { Button } from '../../../../../shared/components/button/button.component';
import { CreditBalanceTrainDialog } from './credit-balance-train-dialog.component';

interface TrainModelProps {
    models: ModelGroupsAlgorithmDetails[];
}

export const TrainModel = ({ models }: TrainModelProps): JSX.Element => {
    const hasModels = !isEmpty(models);
    const [isTrainingDialogOpen, setIsTrainingDialogOpen] = useState<boolean>(false);

    return (
        <>
            <Button
                id={'train-new-model-button-id'}
                data-testid={'train-new-model-button-id'}
                variant={'accent'}
                onPress={() => setIsTrainingDialogOpen(true)}
            >
                Train {!hasModels ? 'new' : ''} model
            </Button>
            <CreditBalanceTrainDialog isOpen={isTrainingDialogOpen} onClose={() => setIsTrainingDialogOpen(false)} />
        </>
    );
};
