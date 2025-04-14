// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface AuthService {
    login: (authToken: string) => Promise<void>;
    logout: () => Promise<void>;
}
