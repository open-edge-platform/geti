// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export interface GlobalStatusDTO {
    free_space: string;
    n_running_jobs: number;
    storage: {
        free_space: number;
        total_space: number;
    };
}
