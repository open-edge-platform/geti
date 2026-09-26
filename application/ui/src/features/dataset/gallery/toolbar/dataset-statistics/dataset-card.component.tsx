// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { ReactNode, useId, useState } from 'react';

import { ActionButton, DialogContainer, dimensionValue, Divider, Flex, Heading } from '@geti-ui/ui';
import { Collapse, Expand } from '@geti-ui/ui/icons';

type DatasetCardProps = {
    title: string;
    gridArea: string;
    children: ReactNode;
    hasFullSizeContent?: boolean;
};

export const DatasetCard = ({ title, gridArea, children, hasFullSizeContent = false }: DatasetCardProps) => {
    const [isFullscreenOpen, setIsFullscreenOpen] = useState(false);
    const headingId = useId();

    return (
        <div role='group' aria-labelledby={headingId} style={{ gridArea }}>
            <Flex
                gap={'size-100'}
                width={'100%'}
                height={'100%'}
                direction={'column'}
                UNSAFE_style={{
                    padding: dimensionValue('size-200'),
                    background: 'var(--spectrum-global-color-gray-100)',
                }}
            >
                <Flex alignItems={'center'} justifyContent={'space-between'}>
                    <Heading id={headingId}>{title}</Heading>

                    {hasFullSizeContent && (
                        <>
                            <ActionButton isQuiet onPress={() => setIsFullscreenOpen(true)}>
                                <Expand />
                            </ActionButton>

                            <DialogContainer type={'fullscreen'} onDismiss={() => setIsFullscreenOpen(false)}>
                                {isFullscreenOpen && (
                                    <Flex
                                        height={'100%'}
                                        gap={'size-200'}
                                        direction={'column'}
                                        UNSAFE_style={{ padding: dimensionValue('size-300') }}
                                    >
                                        <ActionButton
                                            isQuiet
                                            alignSelf={'end'}
                                            onPress={() => setIsFullscreenOpen(false)}
                                            aria-label='collapse fullscreen'
                                        >
                                            <Collapse />
                                        </ActionButton>

                                        {children}
                                    </Flex>
                                )}
                            </DialogContainer>
                        </>
                    )}
                </Flex>
                <Divider size='S' />
                {isFullscreenOpen ? null : children}
            </Flex>
        </div>
    );
};
