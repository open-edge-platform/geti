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

import { FC } from 'react';

import { Button } from '../../../../../../../shared/components/button/button.component';
import { TooltipWithDisableButton } from '../../../../../../../shared/components/custom-tooltip/tooltip-with-disable-button';
import { usePOTModel } from '../../../hooks/use-pot-model/use-pot-model.hook';

interface StartOptimizationProps {
    isModelBeingOptimized: boolean;
    isDisabled: boolean;
    disabledTooltip?: string;
}

export const StartOptimization: FC<StartOptimizationProps> = ({
    isModelBeingOptimized,
    isDisabled,
    disabledTooltip,
}) => {
    const { optimizePOTModel, isLoading } = usePOTModel();

    const handleStartOptimization = (): void => {
        optimizePOTModel();
    };

    return (
        <TooltipWithDisableButton placement={'bottom'} disabledTooltip={disabledTooltip}>
            <Button
                aria-label={isModelBeingOptimized ? 'Optimization in progress' : 'Start optimization'}
                variant={isModelBeingOptimized ? 'secondary' : 'accent'}
                id={'start-optimization-id'}
                onPress={handleStartOptimization}
                isPending={isLoading || isModelBeingOptimized}
                isDisabled={isDisabled}
            >
                Start optimization
            </Button>
        </TooltipWithDisableButton>
    );
};
