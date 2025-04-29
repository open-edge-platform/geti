// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
