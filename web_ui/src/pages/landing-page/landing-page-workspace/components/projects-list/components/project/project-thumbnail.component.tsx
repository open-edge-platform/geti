// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
