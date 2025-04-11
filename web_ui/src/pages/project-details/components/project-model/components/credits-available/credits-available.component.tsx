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

import { Content, ContextualHelp, Flex, useNumberFormatter } from '@adobe/react-spectrum';
import isNil from 'lodash/isNil';

import { CreditCard } from '../../../../../../assets/icons';
import { useCreditsQueries } from '../../../../../../core/credits/hooks/use-credits-api.hook';
import { useProjectIdentifier } from '../../../../../../hooks/use-project-identifier/use-project-identifier';

interface CreditsAvailableProps {
    contextualHelp: string;
}

export const CreditsAvailable = ({ contextualHelp }: CreditsAvailableProps) => {
    const numberFormatter = useNumberFormatter({});
    const projectIdentifier = useProjectIdentifier();

    const { useGetOrganizationBalanceQuery } = useCreditsQueries();
    const { data: creditBalance, isLoading: isLoadingBalance } = useGetOrganizationBalanceQuery({
        organizationId: projectIdentifier.organizationId,
    });

    const creditAvailable = creditBalance?.available;

    if (isLoadingBalance || isNil(creditAvailable)) {
        return <></>;
    }

    return (
        <Flex
            gap={'size-125'}
            width={'100%'}
            marginTop={'size-115'}
            alignItems={'center'}
            justifyContent={'end'}
            UNSAFE_style={{ fontSize: 'var(--spectrum-global-dimension-size-150)' }}
        >
            <CreditCard /> Available {numberFormatter.format(creditAvailable)} credits
            <ContextualHelp variant={'info'} placement={'bottom right'}>
                <Content>{contextualHelp}</Content>
            </ContextualHelp>
        </Flex>
    );
};
