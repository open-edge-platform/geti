// INTEL CONFIDENTIAL
//
// Copyright (C) 2022 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

const defaultFileProps: File = {
    lastModified: 0,
    name: 'fake-file',
    webkitRelativePath: '',
    ...new Blob(['12345'], { type: 'plain/txt' }),
    size: 100,
};

export const mockFile = (props: Partial<File>): File => ({
    ...defaultFileProps,
    ...props,
});

export const mockGlobalFile = (fileName: string, fileSize = 1024): File => {
    const type = `image/${fileName.split('.').at(1)}`;

    jest.spyOn(global, 'File').mockImplementation(function () {
        // @ts-expect-error We dont care about typing "this"
        this.size = fileSize;

        // @ts-expect-error We dont care about typing "this"
        this.name = fileName;

        // @ts-expect-error We dont care about typing "this"
        this.type = type;

        // @ts-expect-error We dont care about typing "this"
        return this;
    });

    return new File([new ArrayBuffer(1)], fileName, { type });
};

export const mockLoadVideoFromFile = (props: Partial<HTMLVideoElement>) => {
    const mockVideo = {
        ...props,
    } as unknown as HTMLVideoElement;

    Object.defineProperty(mockVideo, 'onloadedmetadata', {
        set(callback) {
            callback();
        },
    });

    return mockVideo;
};
