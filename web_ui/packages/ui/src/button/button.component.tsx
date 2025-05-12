// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { FC, PropsWithChildren } from 'react';

export const Button: FC<PropsWithChildren> = ({ children }) => {
    return <button>{children}</button>;
};
