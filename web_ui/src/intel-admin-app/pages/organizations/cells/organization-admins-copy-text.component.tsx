// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, View } from '@geti/ui';
import { Copy } from '@geti/ui/icons';
import { usePress } from 'react-aria';

import { useClipboard } from '../../../../hooks/use-clipboard/use-clipboard.hook';

interface CopyTextProps {
    text: string;
    'aria-label': string;
    'data-testid': string;
    confirmationMessage: string;
}

export const OrganizationAdminsCopyText = (props: CopyTextProps): JSX.Element => {
    const { copy } = useClipboard();
    const { pressProps } = usePress({ onPress: () => copy(props.text, props.confirmationMessage) });

    return (
        //Spectrum-tooltip has buggy position behavior with the tag button; this is a work around
        <div {...pressProps} aria-label={props['aria-label']} style={{ cursor: 'pointer' }} role='button'>
            <Flex gap={'size-100'} data-testid={props['data-testid']} alignItems={'center'}>
                <View>{props.text}</View>
                <Copy />
            </Flex>
        </div>
    );
};
