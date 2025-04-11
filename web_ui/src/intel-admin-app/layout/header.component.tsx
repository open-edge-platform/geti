// INTEL CONFIDENTIAL
//
// Copyright (C) 2023 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Heading, Header as SpectrumHeader } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';

import { IntelLogoTransparent } from '../../assets/images';
import { Navbar } from './navbar.component';

import classes from './layout.module.scss';

export const Header = (): JSX.Element => {
    return (
        <SpectrumHeader UNSAFE_className={classes.header}>
            <Flex height={'100%'} alignItems={'center'} gap={'size-700'} marginX={'size-200'}>
                <Flex alignItems={'center'} gap={'size-300'}>
                    <IntelLogoTransparent />
                    <Heading margin={0} UNSAFE_style={{ fontSize: dimensionValue('size-250'), fontWeight: 'normal' }}>
                        Intel® Geti™ Admin
                    </Heading>
                </Flex>
                <Navbar />
            </Flex>
        </SpectrumHeader>
    );
};
