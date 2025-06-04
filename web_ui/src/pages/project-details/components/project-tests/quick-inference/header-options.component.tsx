// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ReactNode } from 'react';

import { Flex, Heading } from '@geti/ui';

import { FullscreenAction } from '../../../../../shared/components/fullscreen-action/fullscreen-action.component';

interface HeaderOptionsProps {
    fullscreenComponent: ReactNode;
    title: string;
}

export const HeaderOptions = ({ fullscreenComponent, title }: HeaderOptionsProps) => {
    return (
        <Flex alignItems={'center'} justifyContent={'space-between'}>
            <Heading margin={0}>{title}</Heading>
            <Flex>
                <FullscreenAction title={title}>{fullscreenComponent}</FullscreenAction>
            </Flex>
        </Flex>
    );
};
