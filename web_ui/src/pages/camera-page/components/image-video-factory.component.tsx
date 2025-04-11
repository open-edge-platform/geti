// INTEL CONFIDENTIAL
//
// Copyright (C) 2024 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

interface ImageVideoFactoryProps {
    src: string;
    alt?: string;
    style?: React.CSSProperties;
    controls?: boolean;
    className?: string;
    isVideoFile: boolean;
}

export const ImageVideoFactory = ({
    src,
    alt,
    style,
    isVideoFile,
    controls = false,
    ...otherProps
}: ImageVideoFactoryProps): JSX.Element => {
    if (!isVideoFile) {
        return <img src={src} alt={alt} style={style} {...otherProps} />;
    }

    return (
        <>
            {/* eslint-disable-next-line jsx-a11y/media-has-caption */}
            <video preload={'meta'} controls={controls} style={style} {...otherProps}>
                <source src={src} />
            </video>
        </>
    );
};
