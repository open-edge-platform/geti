// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export default async (): Promise<typeof import('../opencv/4.9.0/opencv.js')> => {
    return await import('../opencv/4.9.0/opencv.js');
};
