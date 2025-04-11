// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Text } from '@adobe/react-spectrum';

import { Copy } from '../../../../assets/icons';
import { useClipboard } from '../../../../hooks/use-clipboard/use-clipboard.hook';
import { Button } from '../../../../shared/components/button/button.component';

import classes from '../personal-access-token-page.module.scss';

interface CopyPersonalAccessTokenProps {
    personalAccessToken: string | undefined;
    personalAccessTokenId: string | undefined;
}

export const CopyPersonalAccessToken = ({
    personalAccessToken = '',
    personalAccessTokenId = '',
}: CopyPersonalAccessTokenProps): JSX.Element => {
    const { copy } = useClipboard();

    return (
        <Flex UNSAFE_className={classes.copyKey}>
            <Text
                UNSAFE_style={{ display: 'block' }}
                id='personal-access-token-value-id'
                data-id={personalAccessTokenId}
            >
                {personalAccessToken}
            </Text>
            <Button
                variant={'accent'}
                marginTop={'size-200'}
                id={'copy-api-key-button-id'}
                aria-label={'copy-api-key'}
                UNSAFE_className={classes.copyButton}
                onPress={() => copy(personalAccessToken, 'Personal Access Token copied successfully')}
            >
                <Copy />
                Copy
            </Button>
        </Flex>
    );
};
