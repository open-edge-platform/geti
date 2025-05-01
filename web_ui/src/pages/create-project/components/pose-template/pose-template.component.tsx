// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import { View } from '@adobe/react-spectrum';
import { SliderAnimation } from '@shared/components/slider-animation/slider-animation.component';
import { isNonEmptyString } from '@shared/utils';

import { Alert } from '../../../../assets/icons';
import { RegionOfInterest } from '../../../../core/annotations/annotation.interface';
import { TaskMetadata } from '../../../../core/projects/task.interface';
import { ProjectMetadata } from '../../new-project-dialog-provider/new-project-dialog-provider.interface';
import { getLabelsNamesErrors } from '../../utils';
import { InfoSection } from '../info-section/info-section.component';
import { TemplateManager } from './template-manager.component';
import { getProjectTypeMetadata, TemplateState } from './util';

export interface PoseTemplateProps {
    metadata: TaskMetadata[];
    animationDirection: number;
    updateProjectState: (projectState: Partial<ProjectMetadata>) => void;
}
export const PoseTemplate = ({ metadata, animationDirection, updateProjectState }: PoseTemplateProps) => {
    const keypointStructure = metadata?.at(0)?.keypointStructure;
    const keypointError = getLabelsNamesErrors(keypointStructure?.positions?.map(({ label }) => label) ?? []);

    useEffect(() => {
        return () => updateProjectState({ projectTypeMetadata: [] });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    useEffect(() => {
        return () => updateProjectState({ projectTypeMetadata: [] });
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    const handleTemplateChange = ({ points, edges, roi }: TemplateState & { roi: RegionOfInterest }) => {
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
                    <InfoSection
                        icon={<Alert style={{ fill: 'var(--brand-coral-cobalt)' }} />}
                        marginTop={0}
                        height={'size-275'}
                        message={keypointError}
                    />
                ) : (
                    <View height={'size-275'}></View>
                )}
            </TemplateManager>
        </SliderAnimation>
    );
};
