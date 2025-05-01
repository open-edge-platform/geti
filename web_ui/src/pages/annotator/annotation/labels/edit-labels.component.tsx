// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { Flex } from '@adobe/react-spectrum';
import { dimensionValue } from '@react-spectrum/utils';
import { TaskLabelTreeSearchPopover } from '@shared/components/task-label-tree-search/task-label-tree-search-popover.component';
import { hasEqualId, runWhenTruthy } from '@shared/utils';

import { Annotation } from '../../../../core/annotations/annotation.interface';
import { Label } from '../../../../core/labels/label.interface';
import { isExclusive } from '../../../../core/labels/utils';
import { isAnomalyDomain } from '../../../../core/projects/domains';
import { SelectionIndicator } from '../../components/labels/label-search/selection-indicator.component';
import { AnnotationToolContext } from '../../core/annotation-tool-context.interface';
import { useROI } from '../../providers/region-of-interest-provider/region-of-interest-provider.component';
import { getGlobalAnnotations } from '../../providers/task-chain-provider/utils';
import { useTask } from '../../providers/task-provider/task-provider.component';

interface EditLabelsProps {
    setEditLabels: (editLabels: boolean) => void;
    annotation: Annotation;
    annotationToolContext: AnnotationToolContext;
}

export const EditLabels = ({ annotation, annotationToolContext, setEditLabels }: EditLabelsProps): JSX.Element => {
    const { roi } = useROI();
    const { tasks, selectedTask } = useTask();
    const { addLabel, removeLabels, annotations } = annotationToolContext.scene;

    const isAnomalyTask = selectedTask && isAnomalyDomain(selectedTask?.domain);
    const globalAnnotations = getGlobalAnnotations(annotations, roi, selectedTask);
    const isGlobalAnnotation = globalAnnotations.some(hasEqualId(annotation?.id));

    const filteredTasks = tasks.map((task) => {
        const anomalyValidation = (label: Label) => (isAnomalyTask && !isGlobalAnnotation ? !isExclusive(label) : true);

        return { ...task, labels: task.labels.filter(anomalyValidation) };
    });

    const onLabelSearchClick = runWhenTruthy((label: Label) => {
        const hasLabel = annotation.labels.some(hasEqualId(label.id));

        if (hasLabel) {
            removeLabels([label], [annotation.id]);
        } else {
            addLabel(label, [annotation.id]);
        }

        setEditLabels(false);
    });

    return (
        <div style={{ minWidth: dimensionValue('size-3000') }} onWheelCapture={(event) => event.stopPropagation()}>
            <TaskLabelTreeSearchPopover
                isFocus
                tasks={filteredTasks}
                id={annotation.id}
                selectedTask={selectedTask}
                onClick={onLabelSearchClick}
                onClose={() => setEditLabels(false)}
                textFieldProps={{
                    placeholder: 'Select label',
                    'aria-label': 'Select label',
                }}
                suffix={(label, state) => {
                    const isSelected = annotation.labels.some(hasEqualId(label.id));

                    return (
                        <Flex marginStart={'auto'} alignItems={'center'}>
                            <SelectionIndicator isHovered={state.isHovered} isSelected={isSelected} />
                        </Flex>
                    );
                }}
            />
        </div>
    );
};
