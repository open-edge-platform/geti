// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { type NavigateOptions } from 'react-router-dom';

declare module '@adobe/react-spectrum' {
    interface RouterConfig {
        routerOptions: NavigateOptions;
    }
}
