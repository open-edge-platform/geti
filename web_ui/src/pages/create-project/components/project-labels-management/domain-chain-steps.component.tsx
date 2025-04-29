// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';

import { ChevronRightSmallLight } from '../../../../assets/icons';
import { DomainStepProps } from './domain-step.interface';
import { useDomainButtons } from './use-domain-buttons.hook';

export const DomainChainSteps = (props: DomainStepProps): JSX.Element => {
    const { firstDomainButton, secondDomainButton } = useDomainButtons(props);

    return (
        <Flex alignItems={'center'} gap={'size-50'} marginX={'size-200'} marginBottom={'size-200'}>
            {firstDomainButton}
            <ChevronRightSmallLight />
            {secondDomainButton}
        </Flex>
    );
};
