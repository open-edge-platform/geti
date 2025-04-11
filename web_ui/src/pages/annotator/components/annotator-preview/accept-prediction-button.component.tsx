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
