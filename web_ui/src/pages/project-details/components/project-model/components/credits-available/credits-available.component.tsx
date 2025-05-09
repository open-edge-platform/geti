// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Content, ContextualHelp, Flex, useNumberFormatter } from '@adobe/react-spectrum';
import { isNil } from 'lodash-es';

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
