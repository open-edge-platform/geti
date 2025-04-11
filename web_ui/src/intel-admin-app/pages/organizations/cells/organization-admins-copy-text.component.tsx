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

import { Flex, View } from '@adobe/react-spectrum';
import { usePress } from 'react-aria';

import { Copy } from '../../../../assets/icons';
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
