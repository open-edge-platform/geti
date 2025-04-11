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

import { useEffect } from 'react';

import { View } from '@adobe/react-spectrum';

import { InfoOutline } from '../../../../assets/icons';
import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { SliderAnimation } from '../../../../shared/components/slider-animation/slider-animation.component';
import { isNonEmptyString } from '../../../../shared/utils';
import { ProjectMetadata } from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { InfoSection } from '../info-section/info-section.component';
import { TemplateManager } from './template-manager.component';
import { getProjectTypeMetadata, getValidationError, TemplateState } from './util';

export interface PoseTemplateProps {
    keypointError?: string;
    animationDirection: number;
    setValidationError: (error: string | undefined) => void;
    updateProjectState: (projectState: Partial<ProjectMetadata>) => void;
}

export const PoseTemplate = ({
    keypointError,
    animationDirection,
    updateProjectState,
    setValidationError,
}: PoseTemplateProps) => {
    useEffect(() => {
        setValidationError(getValidationError([]));

        return () => {
            setValidationError(undefined);
        };
    }, [setValidationError]);

    const handleTemplateChange = ({ points, edges, roi }: TemplateState & { roi: RegionOfInterest }) => {
        setValidationError(getValidationError(points));
        updateProjectState({ projectTypeMetadata: [getProjectTypeMetadata(points, edges, roi)] });
    };

    return (
        <SliderAnimation
            animationDirection={animationDirection}
            style={{
                height: '60vh',
                display: 'flex',
                flexDirection: 'column',
                gap: 'var(--spectrum-global-dimension-size-125)',
            }}
        >
            <TemplateManager gap={'size-300'} onTemplateChange={handleTemplateChange}>
                {isNonEmptyString(keypointError) ? (
                    <InfoSection icon={<InfoOutline />} message={keypointError} marginTop={0} height={'size-275'} />
                ) : (
                    <View height={'size-275'}></View>
                )}
            </TemplateManager>
        </SliderAnimation>
    );
};
