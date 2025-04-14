// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

export const SampleImage = ({ url }: { url: string }) => {
    return (
        <img
            src={url}
            alt='sample ref'
            style={{
                objectFit: 'contain',
                width: '100%',
                height: '100%',
                position: 'absolute',
                zIndex: -1,
            }}
        />
    );
};
