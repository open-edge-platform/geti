// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { CSSProperties, useEffect } from 'react';

import { View } from '@adobe/react-spectrum';
import { Loading } from '@shared/components/loading/loading.component';
import { useDrawImageOnCanvas } from '@shared/hooks/use-draw-image-on-canvas.hook';

import { Explanation } from '../../../../core/annotations/prediction.interface';
import { useExplanationOpacity } from '../../providers/prediction-provider/prediction-provider.component';
import { useCachedImages } from './use-cached-images.hook';
import { useInferenceImage } from './use-inference-image.hook';

import classes from './explanation.module.scss';

interface ExplanationProps {
    opacity: number;
    explanation: Explanation | undefined;
    enabled: boolean;
}

const DEFAULT_SIZE = 0;

export const ExplanationMap = ({ explanation, opacity, enabled }: ExplanationProps): JSX.Element => {
    const url =
        explanation === undefined
            ? undefined
            : explanation?.binary
              ? `data:image/jpeg;base64, ${explanation.binary}`
              : `${explanation?.url}?raw=true`;

    const formatter = useInferenceImage(
        explanation?.roi.shape.width ?? DEFAULT_SIZE,
        explanation?.roi.shape.height ?? DEFAULT_SIZE
    );
    const { image, isLoading, load } = useCachedImages({ formatter });
    const ref = useDrawImageOnCanvas({ image, enabled });

    useEffect(() => {
        if (enabled && url !== undefined) {
            load(url);
        }
    }, [url, load, enabled]);

    if (!enabled || !explanation) {
        return <></>;
    }

    const style = {
        opacity: isLoading ? 0 : opacity / 100,
        marginLeft: `${explanation?.roi.shape.x}px`,
        marginTop: `${explanation?.roi.shape.y}px`,
    };

    const loadingStyles = {
        backgroundColor: 'rgba(36 37 40 / 60%)',
        '--spectrum-loader-circle-large-width': 'calc(var(--spectrum-global-dimension-size-800) / var(--zoom-level))',
        '--spectrum-loader-circle-large-height': 'calc(var(--spectrum-global-dimension-size-800) / var(--zoom-level))',
        '--spectrum-loader-circle-large-border-size':
            'calc(var(--spectrum-global-dimension-size-50) / var(--zoom-level))',
    } as CSSProperties;

    return (
        <div className={classes.canvas}>
            <canvas
                id='explanation-image'
                aria-label='explanation image'
                ref={ref}
                data-testid='explanation-image'
                width={explanation?.roi.shape.width}
                height={explanation?.roi.shape.height}
                style={style}
            />
            {isLoading && (
                <View position='absolute' top={0} bottom={0} left={0} right={0} UNSAFE_style={loadingStyles}>
                    <Loading />
                </View>
            )}
        </div>
    );
};

export const ExplanationWithOpacity = (props: { explanation: Explanation | undefined; enabled: boolean }) => {
    const { explanationOpacity } = useExplanationOpacity();

    return <ExplanationMap {...props} opacity={explanationOpacity} />;
};
