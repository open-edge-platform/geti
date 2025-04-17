// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export default async function getCv(self: DedicatedWorkerGlobalScope): Promise<unknown> {
    self.importScripts(new URL('../../public/assets/opencv/4.9.0/opencv.js', import.meta.url).toString());

    return await cv;
}
