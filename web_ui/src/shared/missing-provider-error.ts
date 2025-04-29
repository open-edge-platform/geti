// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export class MissingProviderError extends Error {
    constructor(hook: string, provider: string) {
        super(`${hook} must be used within a ${provider}`);
    }
}
