// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { RefObject, useRef } from 'react';

import { Annotation, KeypointAnnotation } from '../../../../core/annotations/annotation.interface';
import { ShapeType } from '../../../../core/annotations/shapetype.enum';
import { useOutsideClick } from '../../../../hooks/outside-click/outside-click.hook';
import { hasEqualId } from '../../../../shared/utils';
import { isWheelButton } from '../../../buttons-utils';
import { Labels } from '../../annotation/labels/labels.component';
import { ToolType } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { getGlobalAnnotations } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';
import { SelectingToolType } from '../selecting-tool/selecting-tool.enums';
import { ToolAnnotationContextProps } from '../tools.interface';
import { EditBoundingBox as EditBoundingBoxTool } from './edit-bounding-box/edit-bounding-box.component';
import { EditCircle as EditCircleTool } from './edit-circle/edit-circle.component';
import { EditKeypointTool } from './edit-keypoint/edit-keypoint-tool.component';
import { EditPolygon as EditPolygonTool } from './edit-polygon/edit-polygon.component';
import { EditRotatedBoundingBox as EditRotatedBoundingBoxTool } from './edit-rotated-bounding-box/edit-rotated-bounding-box.component';

interface EditAnnotationToolFactoryProps extends ToolAnnotationContextProps {
    annotation: Annotation;
    disableTranslation?: boolean;
    disablePoints?: boolean;
}
const EditAnnotationToolFactory = ({
    annotation,
    annotationToolContext,
    disableTranslation = false,
    disablePoints = false,
}: EditAnnotationToolFactoryProps) => {
    const { roi } = useROI();
    const { tasks, selectedTask } = useTask();
    const task = selectedTask ?? tasks[0];

    const globalAnnotations = getGlobalAnnotations(annotationToolContext.scene.annotations, roi, task);

    if (globalAnnotations.some(hasEqualId(annotation.id))) {
        return <Labels annotation={annotation} annotationToolContext={annotationToolContext} />;
    }

    switch (annotation.shape.shapeType) {
        case ShapeType.Rect: {
            return (
                <EditBoundingBoxTool
                    annotationToolContext={annotationToolContext}
                    annotation={annotation as Annotation & { shape: { shapeType: ShapeType.Rect } }}
                    disableTranslation={disableTranslation}
                    disablePoints={disablePoints}
                />
            );
        }
        case ShapeType.RotatedRect: {
            return (
                <EditRotatedBoundingBoxTool
                    annotationToolContext={annotationToolContext}
                    annotation={annotation as Annotation & { shape: { shapeType: ShapeType.RotatedRect } }}
                    disableTranslation={disableTranslation}
                    disablePoints={disablePoints}
                />
            );
        }
        case ShapeType.Polygon: {
            return (
                <EditPolygonTool
                    annotationToolContext={annotationToolContext}
                    annotation={annotation as Annotation & { shape: { shapeType: ShapeType.Polygon } }}
                    disableTranslation={disableTranslation}
                    disablePoints={disablePoints}
                />
            );
        }
        case ShapeType.Circle: {
            return (
                <EditCircleTool
                    annotationToolContext={annotationToolContext}
                    annotation={annotation as Annotation & { shape: { shapeType: ShapeType.Circle } }}
                    disableTranslation={disableTranslation}
                    disablePoints={disablePoints}
                />
            );
        }

        case ShapeType.Pose: {
            return (
                <EditKeypointTool
                    annotationToolContext={annotationToolContext}
                    annotation={annotation as KeypointAnnotation}
                />
            );
        }
    }
};

interface EditAnnotationToolProps extends EditAnnotationToolFactoryProps {
    canvasRef?: RefObject<SVGSVGElement>;
}

export const EditAnnotationTool = ({
    annotation,
    annotationToolContext,
    disableTranslation = false,
    disablePoints = false,
    canvasRef,
}: EditAnnotationToolProps): JSX.Element => {
    const ref = useRef<HTMLDivElement>(null);
    const { getToolSettings } = annotationToolContext;

    useOutsideClick({
        ref,
        callback: (event) => {
            // The ctrl key and wheelbuttons are used to pan the image, in which
            // case we do not want to stop editing this annotation as the user
            // likely moved the screen to better focus on the annotation
            if (event.ctrlKey || isWheelButton(event)) {
                return;
            }

            // In the selection tool we want to allow users to select more annotations
            // by shift clicking
            if (annotationToolContext.tool === ToolType.SelectTool && event.shiftKey) {
                return;
            }
            //We don't want to deselect Annotation when the user is brushing
            const toolSetting = getToolSettings(ToolType.SelectTool);

            if (toolSetting?.tool !== SelectingToolType.BrushTool) {
                annotationToolContext.scene.unselectAnnotation(annotation.id);
            }
        },
        element: canvasRef,
    });

    return (
        <div ref={ref}>
            <EditAnnotationToolFactory
                annotationToolContext={annotationToolContext}
                annotation={annotation as Annotation & { shape: { shapeType: ShapeType.Rect } }}
                disableTranslation={disableTranslation}
                disablePoints={disablePoints}
            />
        </div>
    );
};
