// Copyright (C) 2022-2025 Intel Corporation
// LIMITED EDGE SOFTWARE DISTRIBUTION LICENSE

import { useEffect } from 'react';

import {
    Content,
    ContextualHelp,
    Dialog,
    DialogTrigger,
    Divider,
    Flex,
    Text,
    useNumberFormatter,
    View,
} from '@geti/ui';
import { isEmpty } from 'lodash-es';

import { ChevronDownLight } from '../../../../../assets/icons';
import { Explanation } from '../../../../../core/annotations/prediction.interface';
import { Task } from '../../../../../core/projects/task.interface';
import { getAverageScore } from '../../../../../core/tests/services/utils';
import { TestImageMediaResult } from '../../../../../core/tests/test-image.interface';
import { NOTIFICATION_TYPE } from '../../../../../notification/notification-toast/notification-type.enum';
import { useNotification } from '../../../../../notification/notification.component';
import { QuietActionButton } from '../../../../../shared/components/quiet-button/quiet-action-button.component';
import { TaskLabelTreeContainer } from '../../../../../shared/components/task-label-tree-search/task-label-tree-container.component';
import { useFilteredTaskMetadata } from '../../../../../shared/components/task-label-tree-search/use-filtered-task-metadata.hook';
import { hasEqualDomain } from '../../../../../shared/utils';
import { ToggleMode } from '../../../../annotator/components/annotator-preview/toggle-mode.component';
import { ANNOTATOR_MODE } from '../../../../annotator/core/annotation-tool-context.interface';
import { selectFirstOrNoneFromList } from '../../../../annotator/providers/prediction-provider/utils';
import { ExplanationPreviewToolbar } from '../../../../annotator/tools/explanation-tool/explanation-preview-toolbar.component';
import { isEqualLabelId, THRESHOLD_TOOLTIP } from '../../project-test/utils';

import classes from './details-preview-header.module.scss';

interface DetailsPreviewHeaderProps {
    mode: ANNOTATOR_MODE;
    tasks?: Task[];
    selectedTask: Task | null;
    testResult?: TestImageMediaResult | undefined;
    explanations?: Explanation[];
    disableActionModes?: boolean;
    setMode: (mode: ANNOTATOR_MODE) => void;
}

export const DetailsPreviewHeader = ({
    mode,
    tasks = [],
    testResult,
    explanations,
    selectedTask,
    disableActionModes = false,
    setMode,
}: DetailsPreviewHeaderProps) => {
    const formatter = useNumberFormatter({ style: 'percent', maximumFractionDigits: 0 });
    const averagedScore = getAverageScore(testResult?.scores ?? []);
    const domainLabels = useFilteredTaskMetadata({
        input: '',
        tasks,
        selectedTask,
        includesEmptyLabels: false,
    });
    const filteredDomainLabels = domainLabels.filter(hasEqualDomain(selectedTask?.domain));

    const { addNotification, removeNotification } = useNotification();

    const isPredictionMode = mode === ANNOTATOR_MODE.PREDICTION;

    useEffect(() => {
        if (disableActionModes) {
            const notificationId = addNotification({
                message: 'Predictions are only available in the active model. Displaying annotations.',
                type: NOTIFICATION_TYPE.INFO,
            });

            return () => removeNotification(notificationId);
        }

        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, []);

    return (
        <Flex
            gap='size-200'
            direction='row'
            justifyContent='space-between'
            aria-label='AnnotatorPreviewToolbar'
            UNSAFE_className={classes.previewToolbar}
        >
            <Flex gap='size-225' alignItems='center'>
                {!isPredictionMode ? (
                    <Text>Annotations</Text>
                ) : (
                    <>
                        <Text>Predictions</Text>

                        {averagedScore && Number.isFinite(averagedScore.value) && (
                            <>
                                <Divider orientation='vertical' size='S' />
                                <Flex gap='size-100' alignItems='center'>
                                    <Text>Model score: {formatter.format(averagedScore.value)}</Text>

                                    <DialogTrigger type='popover' hideArrow>
                                        <QuietActionButton aria-label='labels scores'>
                                            <ChevronDownLight />
                                        </QuietActionButton>
                                        <Dialog UNSAFE_className={classes.dialog}>
                                            <Content width={'size-4600'} maxHeight={'31.2rem'} marginY={'size-125'}>
                                                <TaskLabelTreeContainer
                                                    suffix={(label) => {
                                                        const score = testResult?.scores.find(isEqualLabelId(label.id));
                                                        const percent = score?.value
                                                            ? formatter.format(score.value)
                                                            : 'N/A';

                                                        return <View marginStart={'auto'}>{percent}</View>;
                                                    }}
                                                    ariaLabel='Label score'
                                                    tasksMetadata={filteredDomainLabels}
                                                />
                                            </Content>
                                        </Dialog>
                                    </DialogTrigger>

                                    <ContextualHelp variant={'info'} placement={'bottom'}>
                                        <Content>{THRESHOLD_TOOLTIP}</Content>
                                    </ContextualHelp>
                                </Flex>
                            </>
                        )}
                        {!isEmpty(explanations) && (
                            <>
                                <Divider orientation='vertical' size='S' />
                                <ExplanationPreviewToolbar
                                    explanations={explanations ?? []}
                                    selectedExplanation={selectFirstOrNoneFromList(explanations ?? [])}
                                />
                            </>
                        )}
                    </>
                )}
            </Flex>
            {!disableActionModes && (
                <Flex gap='size-225'>
                    <Divider orientation='vertical' size='S' />
                    <ToggleMode mode={mode} setMode={setMode} />
                </Flex>
            )}
        </Flex>
    );
};
