// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Button } from '@shared/components/button/button.component';

import { useFeatureFlags } from '../../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { useTotalCreditPrice } from '../../../../hooks/use-credits-to-consume.hook';
import { CreditsAvailable } from '../credits-available/credits-available.component';

type ButtonProps = Partial<ComponentProps<typeof Button>>;

interface ButtonCreditsToConsumeProps extends Partial<ButtonProps> {
    taskId: string;
    isLoading: boolean;
    getTooltip: (totalMedias: number) => string;
}

export const ButtonCreditsToConsume = ({
    taskId,
    getTooltip,
    isLoading,
    ...buttonProps
}: ButtonCreditsToConsumeProps) => {
    const { FEATURE_FLAG_CREDIT_SYSTEM } = useFeatureFlags();
    const { isLoading: isLoadingTotalCreditPrice, getCreditPrice } = useTotalCreditPrice();
    const { totalCreditsToConsume, totalMedias } = getCreditPrice(taskId);
    const tooltip = totalMedias ? getTooltip(totalMedias) : '';

    if (FEATURE_FLAG_CREDIT_SYSTEM) {
        return (
            <>
                <TooltipTrigger placement={'top'}>
                    <Button
                        {...buttonProps}
                        variant={'accent'}
                        marginStart={'size-200'}
                        aria-label='credits to consume'
                        id={'start-button-id'}
                        isPending={isLoading || isLoadingTotalCreditPrice}
                    >
                        <Text>Train ({totalCreditsToConsume} credits)</Text>
                    </Button>
                    <Tooltip>{tooltip}</Tooltip>
                </TooltipTrigger>

                <CreditsAvailable contextualHelp={tooltip} />
            </>
        );
    }

    return (
        <Button isPending={isLoading} id={'start-button-id'} {...buttonProps}>
            Start
        </Button>
    );
};
