// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { useState } from 'react';

import { ButtonGroup, Content, Dialog, DialogContainer, Divider, Heading, Text } from '@adobe/react-spectrum';

import { useFeatureFlags } from '../../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Button } from '../../../../../../shared/components/button/button.component';
import { useTotalCreditPrice } from '../../../../hooks/use-credits-to-consume.hook';
import { useTrainStateValue } from '../../train-model-dialog/use-training-state-value/use-training-state-value.hook';

import classes from './model-card.module.scss';

interface ActivateModelDialogProps {
    isOpen: boolean;
    modelName: string;
    modelVersion: number;
    createdAt: string;
    handleDismiss: () => void;
    handleActivateModel: () => Promise<void>;
    handleActivateAndRetrainModel: () => Promise<void>;
}

const TotalCreditsDeduction = () => {
    const { isLoading, getCreditPrice } = useTotalCreditPrice();
    const { selectedTask } = useTrainStateValue();
    const { totalCreditsToConsume } = getCreditPrice(selectedTask.id);
    const displayCreditDeductionInfo = !isLoading;

    return displayCreditDeductionInfo ? (
        <Text UNSAFE_className={classes.creditDeductionInfo}>{totalCreditsToConsume} credits will be deducted.</Text>
    ) : (
        <></>
    );
};

export const ActivateModelDialog = ({
    isOpen,
    modelName,
    createdAt,
    modelVersion,
    handleDismiss,
    handleActivateModel,
    handleActivateAndRetrainModel,
}: ActivateModelDialogProps): JSX.Element => {
    // we need two separate variables to correctly display disabled/loading status of buttons
    const [isActivateLoading, setIsActivateLoading] = useState<boolean>(false);
    const [isActivateRetrainLoading, setIsActivateRetrainLoading] = useState<boolean>(false);
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();

    const onActivateModel = async () => {
        setIsActivateLoading(true);

        await handleActivateModel();

        setIsActivateLoading(false);
    };

    const onActivateRetrainModel = async () => {
        setIsActivateRetrainLoading(true);

        await handleActivateAndRetrainModel();

        setIsActivateRetrainLoading(false);
    };

    return (
        <DialogContainer onDismiss={handleDismiss}>
            {isOpen && (
                <Dialog>
                    <Heading>{`Set the "${modelName}" as active model`}</Heading>
                    <Divider />
                    <Content>
                        <Text id={'activate-model-message-id'} UNSAFE_className={classes.activateDialogMessage}>
                            The selected model - {modelName} - Version {modelVersion} from {createdAt} - was trained
                            with different label sets. Without retraining, the model could return inference results
                            which do not reflect the latest label sets.
                        </Text>
                        {FEATURE_FLAG_CREDIT_SYSTEM && <TotalCreditsDeduction />}
                    </Content>
                    <ButtonGroup>
                        <Button variant={'secondary'} onPress={handleDismiss}>
                            Close
                        </Button>
                        <Button
                            variant={'primary'}
                            aria-label={'Set as active'}
                            id={'set-as-active-id'}
                            data-testid={'set-as-active-id'}
                            onPress={onActivateModel}
                            isPending={isActivateLoading}
                            isDisabled={isActivateRetrainLoading}
                        >
                            Set as active
                        </Button>
                        <Button
                            variant={'accent'}
                            aria-label={'Set as active and retrain'}
                            id={'set-as-active-retrain-id'}
                            data-testid={'set-as-active-retrain-id'}
                            onPress={onActivateRetrainModel}
                            isPending={isActivateRetrainLoading}
                            isDisabled={isActivateLoading}
                        >
                            Set as active & retrain
                        </Button>
                    </ButtonGroup>
                </Dialog>
            )}
        </DialogContainer>
    );
};
