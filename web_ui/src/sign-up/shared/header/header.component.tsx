// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex, View } from '@geti/ui';

import { ReactComponent as Logo } from '../../../assets/geti.svg';

export const Header = (): JSX.Element => {
    return (
        <>
            <View paddingY={'size-350'} position={'relative'} backgroundColor={'gray-300'}>
                <View
                    position={'absolute'}
                    left={0}
                    top={0}
                    width={'size-200'}
                    height={'100%'}
                    backgroundColor={'gray-400'}
                />
                <Flex justifyContent={'center'} alignItems={'center'} columnGap={'size-100'}>
                    <Logo aria-label={'Logo app'} />
                </Flex>
            </View>
            <View position={'relative'}>
                <View width={'size-200'} height={'size-200'} backgroundColor={'gray-300'} />
                <View
                    position={'absolute'}
                    top={'size-200'}
                    left={'size-200'}
                    width={'size-100'}
                    height={'size-100'}
                    backgroundColor={'gray-300'}
                />
            </View>
        </>
    );
};
