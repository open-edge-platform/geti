// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, PropsWithChildren } from 'react';

import { renderHook, RenderHookOptions as RenderHookOptionsBase } from './render-hook';
import { RequiredProviders } from './required-providers-render';

type RenderHookOptionsTemp<Props> = RenderHookOptionsBase<Props> & {
    providerProps?: Omit<ComponentProps<typeof RequiredProviders>, 'children'>;
};

export const renderHookWithProviders = <Result, Props>(
    render: (initialProps: Props) => Result,
    options: RenderHookOptionsTemp<Props> = {}
) => {
    const { providerProps, initialProps, wrapper } = options;
    const Wrapper = wrapper !== undefined ? wrapper : ({ children }: PropsWithChildren<unknown>) => <>{children}</>;

    return renderHook(render, {
        wrapper: ({ children }) => (
            <RequiredProviders {...providerProps}>{<Wrapper>{children}</Wrapper>}</RequiredProviders>
        ),
        initialProps,
    });
};
