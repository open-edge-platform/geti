// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE
export interface WebWorker<T> {
    terminate: () => void;
    optimizePolygon: (value: T) => Promise<T>;
    waitForOpenCV: () => Promise<boolean>;
}
