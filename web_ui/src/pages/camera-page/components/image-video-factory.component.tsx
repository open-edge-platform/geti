// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

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
