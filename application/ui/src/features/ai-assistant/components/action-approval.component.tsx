// Copyright (C) 2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, ButtonGroup, Content, Flex, Heading, InlineAlert, Text } from '@geti-ui/ui';

import type { PendingApproval } from '../types';

interface ActionApprovalProps {
    approval: PendingApproval;
    onResolve: (isApproved: boolean) => void;
}

/**
 * The assistant may read anything, but everything that changes the installation
 * stops here until the user says so.
 */
export const ActionApproval = ({ approval, onResolve }: ActionApprovalProps) => {
    return (
        <InlineAlert variant={'notice'} width={'100%'}>
            <Heading>ChatGPT wants to run an action</Heading>
            <Content>
                <Flex direction={'column'} gap={'size-100'}>
                    <Text>{approval.description}</Text>

                    <ButtonGroup>
                        <Button variant={'secondary'} onPress={() => onResolve(false)}>
                            Decline
                        </Button>
                        <Button variant={'accent'} onPress={() => onResolve(true)} autoFocus>
                            Run it
                        </Button>
                    </ButtonGroup>
                </Flex>
            </Content>
        </InlineAlert>
    );
};
