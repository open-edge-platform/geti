// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps } from 'react';

import { Text, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';

import { useFeatureFlags } from '../../../../../../core/feature-flags/hooks/use-feature-flags.hook';
import { Button } from '../../../../../../shared/components/button/button.component';
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
