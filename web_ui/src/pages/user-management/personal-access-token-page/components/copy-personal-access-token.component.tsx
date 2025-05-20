// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Button, Flex, Text } from '@geti/ui';

import { Copy } from '../../../../assets/icons';
import { useClipboard } from '../../../../hooks/use-clipboard/use-clipboard.hook';

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
