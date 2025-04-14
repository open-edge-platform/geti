// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
