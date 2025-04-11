// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { ComponentProps } from 'react';

import { Provider } from '@adobe/react-spectrum';

import './../assets/index.scss';

import theme from './geti/theme';

export const ThemeProvider = ({ children, router }: ComponentProps<typeof Provider>) => {
    return (
        <Provider
            locale={'en-US'}
            theme={theme}
            colorScheme='dark'
            scale='medium'
            router={router}
            id={'theme-provider'}
        >
            {children}
        </Provider>
    );
};
