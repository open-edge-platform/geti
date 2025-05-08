// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import isNil from 'lodash/isNil';

import { useCreditsQueries } from '../../../../../core/credits/hooks/use-credits-api.hook';
import { useFeatureFlags } from '../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Task } from '../../../../../core/projects/task.interface';
import { useTotalCreditPrice } from '../../../hooks/use-credits-to-consume.hook';
import { useProject } from '../../../providers/project-provider/project-provider.component';
import { NotEnoughCreditsDialog } from '../../common/not-enough-credits-dialog/not-enough-credits-dialog.component';
import { TrainModelDialog as LegacyTrainModel } from '../legacy-train-model-dialog/train-model-dialog.component';
import { TrainModel } from './train-model-dialog.component';

interface CreditBalanceTrainDialogProps {
    task?: Task;
    isOpen: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export const CreditBalanceTrainDialog = (props: CreditBalanceTrainDialogProps): JSX.Element => {
    const { projectIdentifier } = useProject();
    const { FEATURE_FLAG_CREDIT_SYSTEM, FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS } = useFeatureFlags();
    const { useGetOrganizationBalanceQuery } = useCreditsQueries();
    const { getCreditPrice } = useTotalCreditPrice();
    const { data: balance } = useGetOrganizationBalanceQuery(
        { organizationId: projectIdentifier.organizationId },
        { enabled: FEATURE_FLAG_CREDIT_SYSTEM }
    );
    const { totalCreditsToConsume } = getCreditPrice(props.task?.id);
    const TrainModelDialog = FEATURE_FLAG_NEW_CONFIGURABLE_PARAMETERS ? TrainModel : LegacyTrainModel;

    if (!FEATURE_FLAG_CREDIT_SYSTEM) {
        return <TrainModelDialog {...props} />;
    }

    if (isNil(balance) || isNil(totalCreditsToConsume)) {
        return <></>;
    }

    if (balance.available >= totalCreditsToConsume) {
        return <TrainModelDialog {...props} />;
    }

    return (
        <NotEnoughCreditsDialog
            isOpen={props.isOpen}
            onClose={props.onClose}
            creditsToConsume={totalCreditsToConsume}
            creditsAvailable={balance.available}
            message={{
                header: 'Needed for this training:',
                // eslint-disable-next-line max-len
                body: 'You don’t have enough credits to train the model. Get more credits or upgrade your plan by contacting support.',
            }}
        />
    );
};
