// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';

import IntelBrandedLoadingGif from './intel-loading.webp';

export const IntelBrandedLoading = (): JSX.Element => {
    return (
        <Flex justifyContent='center' alignItems='center' height='100vh' direction='column'>
            <img
                src={IntelBrandedLoadingGif}
                // eslint-disable-next-line jsx-a11y/no-noninteractive-element-to-interactive-role
                role='progressbar'
                alt='Loading'
                width={dimensionValue('size-2400')}
                height={dimensionValue('size-2400')}
            />
        </Flex>
    );
};
