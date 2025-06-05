// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export default async (self: DedicatedWorkerGlobalScope): Promise<unknown> => {
    self.importScripts(new URL('../opencv/4.9.0/opencv.js', import.meta.url).toString());

    return await cv;
};
