// Copyright (C) 2025-2026 Intel Corporation
// SPDX-License-Identifier: Apache-2.0

import { Content, Dialog, Flex, Loading } from '@geti-ui/ui';

export const MediaPreviewLoading = () => {
    return (
        <Dialog
            UNSAFE_style={{
                backgroundColor: 'var(--spectrum-global-color-gray-50)',
            }}
        >
            <Content>
                <Flex alignItems={'center'} justifyContent={'center'} height={'100%'} width={'100%'}>
                    <Loading variant={'spinner'} mode={'inline'} />
                </Flex>
            </Content>
        </Dialog>
    );
};
