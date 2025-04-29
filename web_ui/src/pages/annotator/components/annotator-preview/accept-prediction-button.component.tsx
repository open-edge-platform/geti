// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, ReactNode } from 'react';

import isFunction from 'lodash/isFunction';

import { useIsPredictionRejected } from '../../providers/annotation-threshold-provider/annotation-threshold-provider.component';
import { usePrediction } from '../../providers/prediction-provider/prediction-provider.component';
import { PredictionButton } from '../secondary-toolbar/prediction-button.component';

interface AcceptPredictionButtonProps {
    styles?: CSSProperties;
    children: ReactNode;
    isDisabled?: boolean;
    onClose: () => void;
    onSuccess?: () => void;
}

export const AcceptPredictionButton = ({
    styles,
    onClose,
    onSuccess,
    children,
    isDisabled = false,
}: AcceptPredictionButtonProps): JSX.Element => {
    const isPredictionRejected = useIsPredictionRejected();
    const { acceptPrediction, userAnnotationsExist } = usePrediction();

    const acceptAndClose = (merge: boolean) => {
        acceptPrediction(merge, isPredictionRejected);
        onClose();
        isFunction(onSuccess) && onSuccess();
    };

    return (
        <PredictionButton
            styles={styles}
            variant='secondary'
            id='accept-predictions'
            userAnnotationsExist={userAnnotationsExist}
            merge={() => acceptAndClose(true)}
            replace={() => acceptAndClose(false)}
            isDisabled={isDisabled}
        >
            {children}
        </PredictionButton>
    );
};
