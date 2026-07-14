// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Button, Content, Dialog, Flex, Heading } from '@geti-ui/ui';

type MediaPreviewErrorProps = {
    message: string;
    onClose: () => void;
};

export const MediaPreviewError = ({ message, onClose }: MediaPreviewErrorProps) => {
    return (
        <Dialog
            UNSAFE_style={{
                backgroundColor: 'var(--spectrum-global-color-gray-50)',
            }}
        >
            <Content>
                <Flex
                    direction={'column'}
                    gap={'size-200'}
                    alignItems={'center'}
                    justifyContent={'center'}
                    height={'100%'}
                >
                    <Heading level={2} UNSAFE_style={{ textAlign: 'center' }}>
                        Couldn&apos;t load this media item.
                        <br />
                        {message}
                    </Heading>
                    <Button variant={'accent'} onPress={onClose}>
                        Back to dataset
                    </Button>
                </Flex>
            </Content>
        </Dialog>
    );
};
