// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, FC } from 'react';

import { ThemeProvider as Provider } from '@geti/ui/theme';

import '../assets/index.scss';

export const ThemeProvider: FC<Pick<ComponentProps<typeof Provider>, 'router' | 'children'>> = ({
    children,
    router,
}) => {
    return <Provider router={router}>{children}</Provider>;
};
