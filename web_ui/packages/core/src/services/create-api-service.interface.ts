// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { AxiosInstance } from 'axios';

import { API_URLS } from './urls';

export interface CreateApiService<Type> {
    (arg?: { instance: AxiosInstance; router: typeof API_URLS }): Type;
}
