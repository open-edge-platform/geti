// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentType } from 'react';

export type UnwrapProps<T> = T extends ComponentType<infer P> ? P : never;

export type EmptyObject = Record<string, never>;
