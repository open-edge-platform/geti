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

import { useState } from 'react';

interface ProjectThumbnailProps {
    id: string;
    alt: string;
    width?: number;
    height?: number;
    thumbnail: string;
    className: string;
    errorClassName: string;
}

const NO_IMAGE_ICON = '/icons/image-icon.svg';

export const ProjectThumbnail = ({
    id,
    alt,
    thumbnail,
    height,
    width,
    className,
    errorClassName,
}: ProjectThumbnailProps): JSX.Element => {
    const [isImgLoadError, setIsImgLoadError] = useState<boolean>(false);

    const onError = (): void => {
        !isImgLoadError && setIsImgLoadError(true);
    };

    return (
        <img
            id={id}
            alt={alt}
            width={width}
            height={height}
            onError={onError}
            src={isImgLoadError ? NO_IMAGE_ICON : thumbnail}
            className={!isImgLoadError ? className : errorClassName}
        />
    );
};
