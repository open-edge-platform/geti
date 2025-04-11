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

import { Flex, Heading, View } from '@adobe/react-spectrum';

import IntelBrandedLoadingGif from './../../../../assets/images/intel-loading.webp';

export const ModelLoading = ({ isLoadingModel }: { isLoadingModel: boolean }) => {
    return (
        <View
            height={'100%'}
            position={'absolute'}
            left={0}
            top={0}
            right={0}
            bottom={0}
            UNSAFE_style={{
                backgroundColor: 'var(--spectrum-alias-background-color-modal-overlay)',
                zIndex: 10,
            }}
        >
            <Flex direction={'column'} alignItems={'center'} justifyContent={'center'} height='100%' gap='size-100'>
                {/*  eslint-disable-next-line jsx-a11y/img-redundant-alt */}
                <img
                    src={IntelBrandedLoadingGif}
                    // eslint-disable-next-line jsx-a11y/no-noninteractive-element-to-interactive-role
                    role='progressbar'
                    alt='Extracting image features'
                    style={{
                        width: 300,
                        height: 300,
                    }}
                />
                <Heading
                    level={1}
                    UNSAFE_style={{
                        textShadow: '1px 1px 2px black, 1px 1px 2px white',
                    }}
                >
                    {isLoadingModel ? 'Loading image model' : 'Extracting image features'}
                </Heading>
            </Flex>
        </View>
    );
};
