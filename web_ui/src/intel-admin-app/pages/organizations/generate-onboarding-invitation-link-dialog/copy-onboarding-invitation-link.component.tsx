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

import { Flex, Text, View } from '@adobe/react-spectrum';

import { Copy } from '../../../../assets/icons';
import { useClipboard } from '../../../../hooks/use-clipboard/use-clipboard.hook';
import { Button } from '../../../../shared/components/button/button.component';

interface CopyOnboardingInvitationLinkProps {
    onboardingToken: string;
}
export const CopyOnboardingInvitationLink = ({ onboardingToken }: CopyOnboardingInvitationLinkProps) => {
    const { copy } = useClipboard();

    const handleCopyOnboardingInvitationLink = async () => {
        await copy(link, 'Onboarding invitation link copied successfully');
    };

    const link = `${window.location.origin}?signup-token=${onboardingToken}`;

    return (
        <View backgroundColor='gray-50' padding={'size-200'}>
            <Text
                id={'onboarding-token-id'}
                data-testid={'onboarding-token-id'}
                UNSAFE_style={{ display: 'block', width: '100%', wordBreak: 'break-all' }}
            >
                {link}
            </Text>
            <Button onPress={handleCopyOnboardingInvitationLink} marginTop={'size-200'}>
                <Flex alignItems={'center'} gap={'size-100'}>
                    <Copy />
                    Copy
                </Flex>
            </Button>
        </View>
    );
};
