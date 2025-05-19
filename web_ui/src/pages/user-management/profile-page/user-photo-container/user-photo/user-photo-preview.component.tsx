// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ComponentProps, useEffect, useRef } from 'react';

import { useUnwrapDOMRef, View, type DOMRefValue } from '@geti/ui';

import { loadImage } from '../../../../../shared/utils';

import classes from './user-photo.module.scss';

interface UserPhotoPreviewProps {
    userPhoto: string;
    width: ComponentProps<typeof View>['width'];
    height: ComponentProps<typeof View>['height'];
}

export const UserPhotoPreview = ({ userPhoto, width, height }: UserPhotoPreviewProps): JSX.Element => {
    const wrapperRef = useRef<DOMRefValue<HTMLElement>>(null);
    const unwrapRef = useUnwrapDOMRef(wrapperRef);
    const canvasRef = useRef<HTMLCanvasElement>(null);

    useEffect(() => {
        loadImage(userPhoto).then((image) => {
            if (!canvasRef.current || !unwrapRef.current) {
                return;
            }

            const ctx = canvasRef.current.getContext('2d');

            if (ctx === null || ctx === undefined) {
                return;
            }

            const { width: canvasWidth, height: canvasHeight } = unwrapRef.current.getBoundingClientRect();

            canvasRef.current.height = canvasHeight;
            canvasRef.current.width = canvasWidth;

            // center image -> object-fit: cover
            // https://stackoverflow.com/questions/39619967/js-center-image-inside-canvas-element

            const ratio = image.width / image.height;
            let newWidth = canvasWidth;
            let newHeight = newWidth / ratio;

            if (newHeight < canvasHeight) {
                newHeight = canvasHeight;
                newWidth = newHeight * ratio;
            }
            const xOffset = newWidth > canvasWidth ? (canvasWidth - newWidth) / 2 : 0;
            const yOffset = newHeight > canvasHeight ? (canvasHeight - newHeight) / 2 : 0;

            ctx.drawImage(image, xOffset, yOffset, newWidth, newHeight);
        });
    }, [canvasRef, unwrapRef, userPhoto]);

    return (
        <View ref={wrapperRef} width={width} height={height}>
            <canvas
                style={{
                    maxWidth: `var(--spectrum-global-dimension-${width})`,
                    maxHeight: `var(--spectrum-global-dimension-${height})`,
                    minWidth: `var(--spectrum-global-dimension-${width})`,
                    minHeight: `var(--spectrum-global-dimension-${height})`,
                }}
                ref={canvasRef}
                id={'user-photo-preview-id'}
                className={classes.userPhotoPreview}
            />
        </View>
    );
};
