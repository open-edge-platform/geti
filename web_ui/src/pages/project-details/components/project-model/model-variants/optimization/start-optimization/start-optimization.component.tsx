// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC } from 'react';

import { Button } from '@shared/components/button/button.component';
import { TooltipWithDisableButton } from '@shared/components/custom-tooltip/tooltip-with-disable-button';

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
