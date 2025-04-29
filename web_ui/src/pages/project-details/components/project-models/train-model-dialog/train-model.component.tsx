// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
