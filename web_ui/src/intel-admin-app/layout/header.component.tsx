// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { dimensionValue, Flex, Heading, Header as SpectrumHeader } from '@geti/ui';

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
