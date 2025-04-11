// INTEL CONFIDENTIAL
//
// Copyright (C) 2025 Intel Corporation
//
// This software and the related documents are Intel copyrighted materials, and your use of them is governed by
// the express license under which they were provided to you ("License"). Unless the License provides otherwise,
// you may not use, modify, copy, publish, distribute, disclose or transmit this software or the related documents
// without Intel's prior written permission.
//
// This software and the related documents are provided as is, with no express or implied warranties,
// other than those that are expressly stated in the License.

import { Flex, Tooltip, TooltipTrigger } from '@adobe/react-spectrum';
import { Text } from '@react-spectrum/text';

import { Delete, LineMappingLight, Reject } from '../../../../assets/icons';
import { isKeypointAnnotation } from '../../../../core/annotations/services/utils';
import { Divider } from '../../../../shared/components/divider/divider.component';
import { AcceptButton } from '../../../../shared/components/quiet-button/accept-button.component';
import { QuietActionButton } from '../../../../shared/components/quiet-button/quiet-action-button.component';
import { useVisibleAnnotations } from '../../hooks/use-visible-annotations.hook';
import { useZoom } from '../../zoom/zoom-provider.component';
import { ToolAnnotationContextProps } from '../tools.interface';
import { useKeypointState } from './keypoint-state-provider.component';
import { getAnnotationInBoundingBox, getInnerPaddedBoundingBox, mirrorPointsAcrossAxis, PointAxis } from './utils';

export const SecondaryToolbar = ({ annotationToolContext }: ToolAnnotationContextProps) => {
    const { zoomState } = useZoom();
    const visibleAnnotations = useVisibleAnnotations();

    const { scene } = annotationToolContext;
    const keypointAnnotation = visibleAnnotations.find(isKeypointAnnotation);
    const { templatePoints, currentBoundingBox, setCurrentBoundingBox } = useKeypointState();
    const hasAnnotations = keypointAnnotation !== undefined;
    const hasCurrentBoundingBox = currentBoundingBox !== null;

    const handleAcceptAnnotation = () => {
        if (currentBoundingBox === null) {
            return;
        }

        setCurrentBoundingBox(null);
        const annotation = getAnnotationInBoundingBox(
            templatePoints,
            getInnerPaddedBoundingBox(currentBoundingBox, zoomState.zoom)
        );

        scene.replaceAnnotations([{ ...annotation, isSelected: true }]);
    };

    const handleRejectAnnotation = () => {
        setCurrentBoundingBox(null);
        keypointAnnotation && scene.replaceAnnotations([{ ...keypointAnnotation, isSelected: true }], true);
    };

    const handleDeleteAnnotation = () => {
        scene.removeAnnotations(visibleAnnotations);
    };

    const handleMirrorAnnotation = (axis: PointAxis) => {
        if (keypointAnnotation === undefined) {
            return;
        }

        const slippedShape = {
            ...keypointAnnotation.shape,
            points: mirrorPointsAcrossAxis(keypointAnnotation.shape.points, axis),
        };

        scene.replaceAnnotations([{ ...keypointAnnotation, isSelected: true, shape: slippedShape }]);
    };

    return (
        <Flex direction='row' alignItems='center' justifyContent='center' gap='size-125'>
            <Text>Keypoint tool</Text>

            <Divider orientation='vertical' size='S' />

            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    isDisabled={!hasAnnotations || hasCurrentBoundingBox}
                    onPress={handleDeleteAnnotation}
                    aria-label={'delete keypoint annotation'}
                >
                    <Delete height={20} width={20} />
                </QuietActionButton>
                <Tooltip>{`Delete keypoint annotation`}</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    isDisabled={!hasAnnotations || hasCurrentBoundingBox}
                    aria-label={'mirror X-axis'}
                    onPress={() => handleMirrorAnnotation(PointAxis.X)}
                >
                    <LineMappingLight height={20} width={20} />
                </QuietActionButton>
                <Tooltip>Mirror X axis</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger placement={'bottom'}>
                <QuietActionButton
                    isDisabled={!hasAnnotations || hasCurrentBoundingBox}
                    aria-label={'mirror Y-axis'}
                    onPress={() => handleMirrorAnnotation(PointAxis.Y)}
                >
                    <LineMappingLight style={{ transform: 'rotate(90deg)' }} height={20} width={20} />
                </QuietActionButton>
                <Tooltip>Mirror Y axis</Tooltip>
            </TooltipTrigger>

            {hasCurrentBoundingBox && (
                <>
                    <TooltipTrigger placement={'bottom'}>
                        <QuietActionButton
                            aria-label={'reject keypoint annotation'}
                            onPress={handleRejectAnnotation}
                            marginEnd={'size-100'}
                        >
                            <Reject height={20} width={20} />
                        </QuietActionButton>
                        <Tooltip>{`Reject keypoint annotation`}</Tooltip>
                    </TooltipTrigger>

                    <TooltipTrigger placement={'bottom'}>
                        <AcceptButton aria-label={'accept new keypoint annotation'} onPress={handleAcceptAnnotation} />
                        <Tooltip>{'Accept new annotation'}</Tooltip>
                    </TooltipTrigger>
                </>
            )}
        </Flex>
    );
};
