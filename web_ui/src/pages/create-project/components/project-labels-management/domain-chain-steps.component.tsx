// INTEL CONFIDENTIAL
//
// Copyright (C) 2021 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

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
