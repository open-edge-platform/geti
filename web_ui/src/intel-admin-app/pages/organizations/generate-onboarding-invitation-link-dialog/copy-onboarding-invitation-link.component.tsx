// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, Text, View } from '@adobe/react-spectrum';
import { Button } from '@shared/components/button/button.component';

import { Copy } from '../../../../assets/icons';
import { useClipboard } from '../../../../hooks/use-clipboard/use-clipboard.hook';

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
