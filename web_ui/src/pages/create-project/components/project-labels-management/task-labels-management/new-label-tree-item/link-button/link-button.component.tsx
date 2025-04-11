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

import { Flex, Link } from '@adobe/react-spectrum';
import { FlexStyleProps } from '@react-types/shared';

import { InfoTooltip } from '../../../../../../../shared/components/info-tooltip/info-tooltip.component';
import { idMatchingFormat } from '../../../../../../../test-utils/id-utils';

interface LinkButtonProps extends FlexStyleProps {
    text: string;
    isOpen: boolean;
    onOpen: () => void;
    info?: string;
    children: JSX.Element;
}

export const LinkButton = ({ text, info, children, isOpen, onOpen, ...props }: LinkButtonProps): JSX.Element => {
    return (
        <Flex alignItems={'center'} {...props}>
            {isOpen ? (
                children
            ) : (
                <Link
                    variant={'primary'}
                    onPress={() => {
                        onOpen();
                    }}
                    UNSAFE_style={{
                        fontSize: '12px',
                        textDecoration: 'none',
                        minWidth: 'max-content',
                        color: 'var(--spectrum-global-color-gray-900)',
                    }}
                >
                    {text}
                </Link>
            )}

            {info && <InfoTooltip tooltipText={info} id={idMatchingFormat(text)} />}
        </Flex>
    );
};
