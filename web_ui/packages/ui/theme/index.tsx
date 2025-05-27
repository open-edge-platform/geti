// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps } from 'react';

import { Provider } from '@adobe/react-spectrum';

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

export {
    isLargeSizeQuery,
    biggerThanQuery,
    isMediumLargeSizeQuery,
    isExtraLargeSizeQuery,
    smallerThanQuery,
} from './queries';

export { COLOR_MODE } from './color-mode.enum';
