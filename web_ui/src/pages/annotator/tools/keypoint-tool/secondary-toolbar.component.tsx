// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { ActionButton, Divider, Flex, Text, Tooltip, TooltipTrigger } from '@geti/ui';
import { Delete, LineMappingLight, Reject } from '@geti/ui/icons';

import { isKeypointAnnotation } from '../../../../core/annotations/services/utils';
import { labelFromUser } from '../../../../core/annotations/utils';
import { AcceptButton } from '../../../../shared/components/quiet-button/accept-button.component';
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
    const { templateLabels, templatePoints, currentBoundingBox, setCurrentBoundingBox } = useKeypointState();
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

        scene.replaceAnnotations([{ ...annotation, labels: [labelFromUser(templateLabels[0])], isSelected: true }]);
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
                <ActionButton
                    isQuiet
                    isDisabled={!hasAnnotations || hasCurrentBoundingBox}
                    onPress={handleDeleteAnnotation}
                    aria-label={'delete keypoint annotation'}
                >
                    <Delete height={20} width={20} />
                </ActionButton>
                <Tooltip>{`Delete keypoint annotation`}</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    isDisabled={!hasAnnotations || hasCurrentBoundingBox}
                    aria-label={'mirror X-axis'}
                    onPress={() => handleMirrorAnnotation(PointAxis.X)}
                >
                    <LineMappingLight height={20} width={20} />
                </ActionButton>
                <Tooltip>Mirror X axis</Tooltip>
            </TooltipTrigger>

            <TooltipTrigger placement={'bottom'}>
                <ActionButton
                    isQuiet
                    isDisabled={!hasAnnotations || hasCurrentBoundingBox}
                    aria-label={'mirror Y-axis'}
                    onPress={() => handleMirrorAnnotation(PointAxis.Y)}
                >
                    <LineMappingLight style={{ transform: 'rotate(90deg)' }} height={20} width={20} />
                </ActionButton>
                <Tooltip>Mirror Y axis</Tooltip>
            </TooltipTrigger>

            {hasCurrentBoundingBox && (
                <>
                    <TooltipTrigger placement={'bottom'}>
                        <ActionButton
                            isQuiet
                            aria-label={'reject keypoint annotation'}
                            onPress={handleRejectAnnotation}
                            marginEnd={'size-100'}
                        >
                            <Reject height={20} width={20} />
                        </ActionButton>
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
